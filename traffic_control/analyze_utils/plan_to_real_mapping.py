"""
Find matching PlanInstances for Real objects. Supported Real Models are:
TrafficSignReal, AdditionalSignReal and MountReal.
Main entry function for this module is find_and_update_plan_instances_to_reals.

Intended use is from django management shell. If going to be used eg. from management command prints should be
replaced with actual logging.
"""

import csv
from operator import countOf

from django.contrib.gis.db.models.functions import Distance
from django.db.models import F, Q, Value
from django.utils import timezone

from traffic_control.db_utils import SplitPart
from traffic_control.enums import Lifecycle
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    MountPlan,
    MountReal,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.services.additional_sign import additional_sign_plan_get_current
from traffic_control.services.mount import mount_plan_get_current
from traffic_control.services.traffic_sign import traffic_sign_plan_get_current


def get_mountreal_to_mountplan_mapping(max_distance: float):
    """Get a list of possible matching MountPlans for a MountReal within given distance"""
    mr_qset = (
        MountReal.objects.active()
        .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
        .filter(
            Q(validity_period_start__isnull=True)
            | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
        )
        .filter(mount_type__isnull=False)
        .filter(mount_plan__isnull=True)
        .select_related("mount_type")
    )

    mr_to_plan_instance = {}
    not_found_for_mrs = []

    for mr in mr_qset:
        plan_instances = MountPlan.objects.exclude(
            id__in=_get_already_referenced_plan_instances(MountReal, "mount_plan")
        ).filter(location__distance_lte=(mr.location, max_distance), mount_type__code=mr.mount_type.code)
        if not plan_instances.exists():
            not_found_for_mrs.append(str(mr.id))
        else:
            mr_to_plan_instance[str(mr.id)] = plan_instances.values_list("id", flat=True)

    return mr_to_plan_instance, not_found_for_mrs


def get_additionalsignreal_to_additionalsignplan_mapping(max_distance: float):
    """Get a list of possible matching AdditionalSignPlans for a AdditionalSignReal within given distance"""
    adsr_qset = (
        AdditionalSignReal.objects.active()
        .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
        .filter(
            Q(validity_period_start__isnull=True)
            | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
        )
        .filter(additional_sign_plan__isnull=True)
        .select_related("device_type", "parent__device_type")
    )

    adsr_to_plan_instance = {}
    not_found_for_adsr = []
    for adsr in adsr_qset:
        plan_instances = AdditionalSignPlan.objects.exclude(
            id__in=_get_already_referenced_plan_instances(AdditionalSignReal, "additional_sign_plan")
        ).filter(
            location__distance_lte=(adsr.location, max_distance),
            device_type__code__in=[adsr.device_type.code, adsr.device_type.legacy_code],
            parent__device_type__code__in=[adsr.parent.device_type.code, adsr.parent.device_type.legacy_code],
        )
        if not plan_instances.exists():
            not_found_for_adsr.append(str(adsr.id))
        else:
            adsr_to_plan_instance[str(adsr.id)] = plan_instances.values_list("id", flat=True)
    return adsr_to_plan_instance, not_found_for_adsr


def get_trafficsignreal_to_trafficsignplan_mapping(max_distance: float):
    """Get a list of possible matching TrafficSignPlans for a TrafficSignReal within given distance"""
    tsr_qset = (
        TrafficSignReal.objects.active()
        .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
        .filter(
            Q(validity_period_start__isnull=True)
            | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
        )
        .filter(traffic_sign_plan__isnull=True)
        .select_related("device_type")
    )

    tsr_to_plan = {}
    not_found_for_tsr = []
    for tsr in tsr_qset:
        plan_instances = TrafficSignPlan.objects.exclude(
            id__in=_get_already_referenced_plan_instances(TrafficSignReal, "traffic_sign_plan")
        ).filter(
            location__distance_lte=(tsr.location, max_distance),
            device_type__code__in=[tsr.device_type.code, tsr.device_type.legacy_code],
        )
        if not plan_instances.exists():
            not_found_for_tsr.append(str(tsr.id))
        else:
            tsr_to_plan[str(tsr.id)] = plan_instances.values_list("id", flat=True)

    return tsr_to_plan, not_found_for_tsr


def _get_already_referenced_plan_instances(real_model, plan_instance_field_name):
    """Get ids query of PlanInstances that are already mapped to some real objects"""
    return real_model.objects.exclude(**{f"{plan_instance_field_name}__isnull": True}).values_list(
        f"{plan_instance_field_name}__id", flat=True
    )


def find_and_update_plan_instances_to_reals(
    real_model, plan_instance_model, plan_instance_field_name, max_distance: float, do_db_update=False
):
    """This is the main function that can be called to do the mapping"""
    reals_to_plan_instances, _ = _get_real_to_plan_instance_mapping(real_model, max_distance)
    unique_ids, _, possible_reals_by_pi_id = get_duplicate_plan_instance_ids(reals_to_plan_instances)
    mapped_reals_to_plan_instances, skipped_real_ids = update_plan_instances_to_reals(
        real_model, plan_instance_model, plan_instance_field_name, reals_to_plan_instances, unique_ids, do_db_update
    )
    all_possible_pids_for_mapped_rids = _get_all_possible_pids_for_mapped_rids(
        mapped_reals_to_plan_instances, reals_to_plan_instances
    )

    if _needs_to_be_run_again(
        skipped_real_ids, reals_to_plan_instances, all_possible_pids_for_mapped_rids, do_db_update
    ):
        # Only can be done when db is actually updated, will endup in infinite recursion loop if the actual database
        # update is not done.
        new_mapped_reals_to_plan_instances, _, skipped_real_ids = find_and_update_plan_instances_to_reals(
            real_model, plan_instance_model, plan_instance_field_name, max_distance, do_db_update=do_db_update
        )
        mapped_reals_to_plan_instances.update(new_mapped_reals_to_plan_instances)

    return mapped_reals_to_plan_instances, possible_reals_by_pi_id, skipped_real_ids


def _needs_to_be_run_again(skipped_real_ids, reals_to_plan_instances, all_possible_pids_for_mapped_rids, do_db_update):
    """Needs to be run again if possible pids for any skipped real id has intersection with just mapped real
    original possibibilies as now the possible pids for a skipped real can actually be unique"""
    if not do_db_update:
        return False
    for skipped_real_id in skipped_real_ids:
        skipped_possible_pids = set(reals_to_plan_instances.get(skipped_real_id))
        pids_intersection = all_possible_pids_for_mapped_rids.intersection(skipped_possible_pids)
        if pids_intersection:
            print(f"Skipped real id: {skipped_real_id} possible pids: {skipped_possible_pids}")
            print(f"intersection possible pids: {pids_intersection}")
            print("Running mapping again...")
            return True
    return False


def _get_all_possible_pids_for_mapped_rids(mapped_reals_to_plans, reals_to_plan_instances):
    """reals_to_plan_instances contains all possible plan instances for a real"""
    all_possible_pids_for_mapped_rids = set()
    for rid in mapped_reals_to_plans.keys():
        all_possible_pids_for_mapped_rids.update(set(reals_to_plan_instances.get(rid)))
    return all_possible_pids_for_mapped_rids


def get_duplicate_plan_instance_ids(real_to_plan_instance_mapping_dict):
    """
    Return tuple where first item is a set of unique plan ids, second item a set of duplicate ids.
    """
    unique_ids = set()
    duplicate_ids = set()
    possible_reals_by_pi_id = {}
    for k, v in real_to_plan_instance_mapping_dict.items():
        for p_id in v:
            if p_id in unique_ids:
                duplicate_ids.add(p_id)
                possible_reals_by_pi_id[str(p_id)].append(str(k))
            else:
                possible_reals_by_pi_id[str(p_id)] = [str(k)]
                unique_ids.add(p_id)
    return unique_ids - duplicate_ids, duplicate_ids, possible_reals_by_pi_id


def _get_real_to_plan_instance_mapping(real_model, max_distance: float):
    if real_model is MountReal:
        return get_mountreal_to_mountplan_mapping(max_distance)
    elif real_model is AdditionalSignReal:
        return get_additionalsignreal_to_additionalsignplan_mapping(max_distance)
    elif real_model is TrafficSignReal:
        return get_trafficsignreal_to_trafficsignplan_mapping(max_distance)
    raise NotImplementedError(f"No implementation for {real_model}")


def update_plan_instances_to_reals(
    real_model,
    plan_instance_model,
    plan_instance_field_name,
    real_to_plan_instance_mapping_dict,
    unique_plan_ids,
    do_db_update,
):
    """Update real object with given plan. If there are multiple choices, then update is skipped.
    If plan id is not in the given unique_plan_ids, then update is skipped.
    """
    real_to_plan_instances = {}
    skipped_real_ids = set()
    for real_id, plan_ids in real_to_plan_instance_mapping_dict.items():
        only_unique_plan_ids = set(plan_ids).intersection(unique_plan_ids) if do_db_update else plan_ids
        plan_instance = _get_best_matching_plan_instance(real_id, real_model, only_unique_plan_ids, plan_instance_model)
        if plan_instance is not None:
            real_to_plan_instances[real_id] = plan_instance
        else:
            skipped_real_ids.add(str(real_id))

    if do_db_update:
        for rid, pi in real_to_plan_instances.items():
            try:
                if pi is not None:
                    real_model.objects.filter(id=rid).update(**{plan_instance_field_name: pi.id})
            except Exception as e:
                print(f"failed to update rid: {rid} plan instance to plan: {pi}: {e}")

    return real_to_plan_instances, skipped_real_ids


def _get_best_matching_plan_instance(real_id, real_model, plan_instance_ids, plan_model):
    """Get one best matching plan for given Real object
    Simple case is when there is only one possible planinstance
    Incase of multiple possible planinstances, closest one is selected. If there are many with the same distance, then
    separate resolution is done in function _get_best_matching_plan_instance
    """
    real_obj = real_model.objects.get(pk=real_id)
    plan_instances = list(
        plan_model.objects.filter(id__in=plan_instance_ids)
        .annotate(
            distance=Distance("location", real_obj.location),
            plan_decision_id=F("plan__decision_id"),
            plan_decision_year=SplitPart(F("plan__decision_id"), Value("-"), 1),
            plan_decision_number=SplitPart(F("plan__decision_id"), Value("-"), 2),
        )
        .order_by("distance", "-created_at")
    )

    if len(plan_instances) == 0:
        return None

    if len(plan_instances) == 1:
        return plan_instances[0]
    else:
        shortest_distance = plan_instances[0].distance
        same_distances = list(filter(lambda x: x.distance == shortest_distance, plan_instances))
        if len(same_distances) == 1:
            return same_distances[0]
        else:
            return _get_same_distance_plan_instance(same_distances)


def _get_same_distance_plan_instance(same_distances):
    """Try to find one plan instance based on plans decision id.
    Decision id format is assumed to be <year>-<running_number>

    Return latest version, first by year and secondary by the running number.
    """
    for pi in same_distances:
        print(
            f"distance: {pi.distance} decision_id: {pi.plan_decision_id} dy: {pi.plan_decision_year}"
            f" dn: {pi.plan_decision_number} for {pi.__class__} id: {pi.id}"
        )
    sorted_by_decision_year_and_number = sorted(
        same_distances, key=lambda x: (x.plan_decision_year, x.plan_decision_number), reverse=True
    )
    mapped_pi_info = map(
        lambda x: (x.plan_decision_year, x.plan_decision_number, x.id), sorted_by_decision_year_and_number
    )
    print(f"sorted_by_decision_year_and_number: {list(mapped_pi_info)}")
    return sorted_by_decision_year_and_number[0]


def find_duplicate_plan_instances(plan_instance_model):
    """Helper function to find plan instances that are almost the same.
    Main usage is from manage shell to help in problematic cases. If this is ever going to be used in real code
    prints should be replaced with actual logging.
    """
    if plan_instance_model is MountPlan:
        queryset = _get_mount_plan_queryset()
    elif plan_instance_model is AdditionalSignPlan:
        queryset = _get_additional_sign_plan_queryset()
    elif plan_instance_model is TrafficSignPlan:
        queryset = _get_traffic_sign_plan_queryset()
    else:
        raise NotImplementedError(f"No implementation for {plan_instance_model} duplicate find")
    print(f"Objects to check {plan_instance_model.objects.count()} for {plan_instance_model}")
    results = {}
    for plan_i in queryset:
        if plan_i.id not in results:
            values_q = (
                queryset.exclude(id=plan_i.id)
                .filter(**_get_match_params(plan_i))
                .values_list("id", "location", "device_type__code")
            )
            if values_q.exists():
                results[str(plan_i.id)] = list(values_q)
        else:
            print(f"Already found duplicates for {plan_i.id}")
    return results


def _get_mount_plan_queryset():
    """Helper function for find_duplicate_plan_instances"""
    return (
        mount_plan_get_current()
        .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
        .filter(
            Q(validity_period_start__isnull=True)
            | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
        )
        .select_related("mount_type")
    )


def _get_additional_sign_plan_queryset():
    """Helper function for find_duplicate_plan_instances"""
    return (
        additional_sign_plan_get_current()
        .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
        .filter(
            Q(validity_period_start__isnull=True)
            | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
        )
        .select_related("device_type")
    )


def _get_traffic_sign_plan_queryset():
    """Helper function for find_duplicate_plan_instances"""
    return (
        traffic_sign_plan_get_current()
        .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
        .filter(
            Q(validity_period_start__isnull=True)
            | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
        )
        .select_related("device_type")
    )


def _get_match_params(plan_instance_obj):
    """Helper function for find_duplicate_plan_instances"""
    params = {"location": plan_instance_obj.location, "plan__id": plan_instance_obj.plan.id}
    if not isinstance(plan_instance_obj, MountPlan):
        params.update(
            {
                "device_type__code__in": [
                    plan_instance_obj.device_type.code,
                    plan_instance_obj.device_type.legacy_code,
                ],
                "mount_plan": plan_instance_obj.mount_plan,
            }
        )
    else:
        params.update({"mount_type__code": plan_instance_obj.mount_type.code})
    return params


def write_results_to_csv(results, real_model, file_path):
    headers = _get_csv_headers(real_model)
    with open(file_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        writer.writerow(headers)
        writer.writerows(_rows_for_results_csv(results, real_model))


def _get_csv_headers(real_model):
    base_headers = [
        "real_id",
        "real_location",
        "pi_id",
        "pi_location",
        "pi_distance",
        "pi_count",
        "pi_frequency",
    ]
    if real_model is TrafficSignReal:
        base_headers.extend(["code", "mount_real", "pi_mount_plan"])
    elif real_model is AdditionalSignReal:
        base_headers.extend(["code", "parent", "additional_information"])
    elif real_model is MountReal:
        base_headers.append("mount_type")
    return base_headers


def _rows_for_results_csv(results, real_model):
    """Get one row for results csv. results is in the format returned by find_and_update_plan_instances_to_reals"""
    pi_counts_per_pi_id = _get_pi_counts(results)
    pi_count_freqs = _get_pi_count_frequencies(pi_counts_per_pi_id)
    for rid, pi in results.items():
        real_obj = real_model.objects.get(id=rid)
        pi_count = pi_counts_per_pi_id[str(pi.id)]
        pi_frequency = pi_count_freqs[pi_count] * pi_count
        # *pi_count looks odd but this need to be done, because pi_ids (keys) pi_counts_per_pi_id exist there only once
        # but in the whole data there can be several rows and pi_count is the number of occurences of the corresponding
        # pi_id

        base_row = [
            str(real_obj.id),
            real_obj.location.ewkt,
            str(pi.id),
            pi.location.ewkt,
            str(pi.distance).split()[0],
            str(pi_count),
            str(pi_frequency),
        ]
        if real_model is TrafficSignReal:
            base_row.extend([real_obj.device_type.code, str(real_obj.mount_real_id), str(pi.mount_plan_id)])
        elif real_model is AdditionalSignReal:
            base_row.extend([real_obj.device_type.code, str(real_obj.parent_id), real_obj.additional_information])
        elif real_model is MountReal:
            base_row.append(str(real_obj.mount_type))

        yield base_row


def _get_pi_counts(results):
    """Get how many times a planinstance id is found as a result value"""
    print("Calculating pi_counts")
    pi_counts_per_pi_id = {}
    pi_ids = list(map(lambda x: str(x.id), results.values()))
    for pi_id in pi_ids:
        if pi_id not in pi_counts_per_pi_id:
            pi_counts_per_pi_id[pi_id] = countOf(pi_ids, pi_id)
    return pi_counts_per_pi_id


def _get_pi_count_frequencies(pi_counts):
    """Get how many times pi_count is found
    eg. if pi_count == 1 is found 5000 times, and pi_count==2 is found 1000 times return value would be:
    {1:5000, 2:1000}
    """
    print("Calculating pi_frequencies")
    pi_count_frequencies = {}
    for count in pi_counts.values():
        if count not in pi_count_frequencies:
            pi_count_frequencies[count] = countOf(pi_counts.values(), count)
    return pi_count_frequencies
