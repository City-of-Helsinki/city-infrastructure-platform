# Changelog

## [1.25.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.24.0...city-infrastructure-platform-v1.25.0) (2025-11-10)


### Features

* Add example local_settings.py file ([798918c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/798918cc9093e82a3fdfdf25a98ae8787aba6f30))
* Gate access to files in FileProxyView ([95d8522](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/95d8522a482bb5f5c59078089a6bfa2c09bdd58b))
* Make files uploads optionally public, handle permissions in api ([a905561](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/a90556117c948a942fdfe7d4f108b28a67778b7a))
* Management command to update planinstance validity periods from plan decision_date ([989cfe4](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/989cfe4105641117f756e7ca6993eec53ceef2d1))
* Set validity_period_start to ValidityPeriodModel object's plan's decision_date ([f293420](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/f293420a54a89271fb7ab6a8e08d751944cad1f8))
* Support for loggging related models changes to parent model's auditlog ([e7469dd](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/e7469dde106048b8f0ed666d6f78deb46d2c65c3))
* Update validity_period_start when setting related plan instances to a plan from admin UI ([d005e19](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d005e19e3909694a47cfe7f8586116e6b86c0dd5))
* When plan is updated, update all related planinstance validity_period_start, if they support it ([4d32a03](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/4d32a03a8d36913f8675755f88aff3d1da601188))

## [1.24.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.23.0...city-infrastructure-platform-v1.24.0) (2025-10-30)


### Features

* Add an arrow pointing to a features direction ([920e3af](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/920e3af89d813a2c59bd18c6346ee36e4348cb3b))
* Add import export for TrafficControlDeviceTypeIcon ([292e27d](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/292e27d96c900a04ced0fd87b6c5df85a4810550))
* Add TrafficControlDeviceType and CityFurnitureDeviceType Icons to audit log ([ee36a5b](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/ee36a5b76a235ccb3b68c067d7067d7a7a5fe45e))
* Remove icon field from city_furniture application ([5dbc022](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/5dbc022169eb48f21737a2afd35b33c9c66334d3))
* Remove icon field from traffic_control appilcation ([174d2cd](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/174d2cd184709debce0a39094249b5d1b6ff53af))
* Remove obsolete command for importing TrafficControlDeviceTypes ([12c2fae](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/12c2fae18fef3b7cf3bbabb6b784fe666f4e36d2))
* Remove old obsolete management command for importing city_furniture_device_types ([92b64df](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/92b64df604fc4e6cd1ee3a86ae28bb90c9f46f7f))
* Remove png generation from build phase ([0112a0c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/0112a0ca4154ca01b4cf18fd8018b12f05c2cdff))
* Remove svg icons from repository ([307acc3](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/307acc35fdd25c5ec27213da2d153ebc8d53080a))
* Remove tests for updating device type icon field ([237d8e5](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/237d8e59f97903e49abb8e397ede4243fd6331a7))


### Bug Fixes

* Audit log does not show user of the action if done via REST and with JWTToken authentication ([7f3f9ee](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/7f3f9eec0a0baa4647114520e6591b8bae48fab6))
* Changing objects responsible entity fix ([38014f1](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/38014f17816cbd8df72ed966d51ecca6d8d894ae))
* Show error note in TrafficControlDeviceTypeIcon also in case with already existing icon ([dd5bd56](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/dd5bd568ac69f188668413c8ddcf39d2381ec27a))

## [1.23.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.22.0...city-infrastructure-platform-v1.23.0) (2025-10-13)


### Features

* Use blobstorage icons in additional and trafficsign listing pages ([c84caad](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/c84caadd2634b0b04af360158288194801c06640))
* Use blobstorage icons in map-view ([51286ce](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/51286ce92578e2dbcc5c7f7fc9778dbced78fff4))
* Use blobstorage icons location for in REST API ([82a4f16](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/82a4f163e4bf2f1a157b20ef3155d47a7666f8e1))


### Bug Fixes

* Force unittest to use english translations ([a221e60](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/a221e60c556d3eb33660b74c4769ebe94b661b01))
* Layer with no matching plan or real layer cannot be disabled ([bcf07e7](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/bcf07e7de8ae826196ac8ee2d639a974c4281a65))
* Selected feature stays visible features layer is disabled. ([e5acd87](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/e5acd8705718d0679cc3f197faf32dc6484f893b))
* Traffic control device type icon not enforcing uniqueness ([9952815](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/9952815af8aed4a1b9852ff30319d6be706531d0))

## [1.22.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.21.0...city-infrastructure-platform-v1.22.0) (2025-10-01)


### Features

* Add icon upload support for traffic sign device types ([6d4c88b](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/6d4c88b99226db5bc1da0923a1835264be88258c))
* Add icon_file field to CityFurnitureDeviceType, override form widget ([01e9340](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/01e9340e5cd35073c9c1832835e9afe575ae7f6d))
* Add signal handlers for city_furniture / traffic_control icon deleted ([4aca0ac](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/4aca0accedc23ba93996ea07183240b261791fb4))
* Enable usage of azurite for locally testing blobstorage operations ([0aef58c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/0aef58c66ced65b12d05df2d5e9f944aa30cf29d))
* Generate PNG icons for city_furniture icons upon SVG icon upload ([498f610](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/498f61096f98d77a3af253611a0683619e7da943))
* Improve dropdown selector for the icon_file field ([11e3d12](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/11e3d12ab36d6cea8a35b7a643048c38b4e04446))
* Management commands for icon upload, device type object fixes ([491831f](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/491831fe34cf26934179252d419a37870c63e61f))
* Scan incoming icon files for viruses ([22f30f4](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/22f30f434de0de304d6b47acc8b46c2fe65c61a6))
* Separate icon storage, enable overwrite, enforce unique filename ([d0e6f1d](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d0e6f1d42f8f0da9997ca2d28d098494c4751c66))


### Bug Fixes

* UI crash condition on the dropdown selector with icon preview ([cfaaa11](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/cfaaa11a877e3880aa79e090665c87765b079025))

## [1.21.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.20.0...city-infrastructure-platform-v1.21.0) (2025-09-26)


### Features

* Allow BARRIER and SIGNPOST target_model devicetypes for TrafficSignReal and Plan objects ([967a3e6](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/967a3e6bd3d951b7ed203e10c42b27d53e4439df))


### Bug Fixes

* Update sonarqube-scan-action version ([e1c6d29](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/e1c6d29341bc70a762450e50fe47c0bdbc47b849))

## [1.20.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.19.0...city-infrastructure-platform-v1.20.0) (2025-09-16)


### Features

* Add double_sided to admin models for trafficsign and signpost, both plans and reals. ([3356fb0](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/3356fb0eabf6e268ff3aa6ab573040e6650c7d6e))
* Add full git sha1 to django admin footer ([80d91ff](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/80d91ffd6c55c91ce840b7a0b0e1fc29b496a090))
* Add transparency to a selected feature ([af090fd](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/af090fde525e1198e99101e2a13c6425336b6545))
* Address search to map view ([4e1f980](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/4e1f9800186f4813de017d3446c793da9e1a47fc))
* Convert App.tsx to function component ([3bbb21c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/3bbb21cc35c217a9644c44f57f2246d8b726a8fb))
* Convert FeatureInfo.tsx to function component ([8aed04c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/8aed04ce91124ab8ab2fe794c62e01019e48f7dd))
* Convert LayerSwitcher to function component ([d3e5d9c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d3e5d9c083e88fd143180bb2baadefa0953baf15))
* Do not allow height edit for linked additional sign real nor plans ([766a2a6](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/766a2a68c809c1426e6f113462dd68934b4409e3))
* Double sided boolean for trafficsign and signpost plans and reals ([13fa4d4](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/13fa4d49a5c7dcaa47f33e9faa813ea3bc6d40f0))
* Remove order fields from all models that have it ([1905eb9](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/1905eb93e924ac22f04ef5782dae76e4c65e1978))


### Bug Fixes

* Correct Address search localization for finnish and swedish ([53228a3](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/53228a33f33f90f92f1cec5f39d9424e2aa8be7d))

## [1.19.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.18.2...city-infrastructure-platform-v1.19.0) (2025-08-29)


### Features

* Add loading indicator when features are being fetched ([a5a6f06](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/a5a6f06c1961561f60bacebeb6cfc04a301bc4d2))
* Add location specifier to MountRealAdmin ([38da4a2](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/38da4a214f047de4197652d7040cacfb6af8888a))
* Add swedish description to MountType model ([d08d9bf](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d08d9bfe3d52ab21bba6b6a415922284cd64edc5))
* Cumulative feature loading based on current view bounding box ([d55c742](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d55c742ac3263c6aecabd2f1cb213370139c204a))
* TraffiControl and CityFurnitureDeviceTypes can now be search by description (fi, sw, en) fields ([dec740d](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/dec740d8592e2173939793f01e7067f676b81bd3))

## [1.18.2](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.18.1...city-infrastructure-platform-v1.18.2) (2025-08-15)


### Bug Fixes

* Use base image that is tagged for debian bookworm version (12) ([7cd9847](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/7cd9847f675db7514b7ee4ca40ef826d679a1a4f))

## [1.18.1](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.18.0...city-infrastructure-platform-v1.18.1) (2025-08-12)


### Bug Fixes

* Add lazy-apps = true to uwsgi start up ([a357b70](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/a357b70f292b33e80c2f869304c94805e1775549))
* Add py-call-uwsgi-fork-hooks = true to uwsgi start parameters ([5282593](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/52825939ed4bb08d43915e598f553ca02b87003e))

## [1.18.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.17.0...city-infrastructure-platform-v1.18.0) (2025-08-11)


### Features

* Highlight selected feature in map-view ([8fddb05](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/8fddb05784bc676cb35636bebd31d01cd11aaf19))
* Management command to print target_model validity checks ([7831ac0](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/7831ac0263dd7faceaf0ac107152e6e557ca2658))


### Bug Fixes

* Change order of highlight and planofreal layers ([b36f911](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/b36f911354dce4b408171d93e97b7693e3c1e234))
* Difference drawing did not work for nonclustered layers ([09a4d43](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/09a4d4370d6ffbfff847dc331adc3b234063a938))
* Difference drawing did not work properly when 2 or more real-plan pairs were activated ([3177840](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/317784090779c7571d5c7a579ad3f912e0cf5d1f))
* Disabling layer with no real-plan mapping ([d837fe4](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d837fe4666d519dc8e815701583fa3fe372ec729))
* Missing mount_type filter from MountReal admin page ([10ce03f](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/10ce03fae5056c2801f7257c2841d9d65479459b))
* Show helfpul error when invalid target data model is selected ([7859505](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/7859505f3b49a29ebdf07f2af1df56d1516a7d4f))

## [1.17.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.16.0...city-infrastructure-platform-v1.17.0) (2025-06-12)


### Features

* Add mount_type to Mount admin filters ([63e1a4d](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/63e1a4dd6badedda4bbb24c8c4a24c553832133e))
* Add support to order FeatureInfo extra fields ([5d31797](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/5d317978d0227a7807f9a85c38363d1a61889180))

## [1.16.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.15.0...city-infrastructure-platform-v1.16.0) (2025-06-10)


### Features

* Change active field name to enabled in IconDrawConfig model ([7945bdc](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/7945bdc64d08134d5f5f12b99476625730356083))
* Dynamic configuration for map-view FeatureInfos by layer ([8c44e19](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/8c44e190713cddc2dde4704d27406b80d349ac48))
* Replace seasonal validity period date fields with one information field ([42cbfb2](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/42cbfb23dae4e1fe2eae733a7afbe139936c2a09))
* Z_coord can now be optional ([e840e98](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/e840e984acb73b7170d7563f4d34eec01b8cbae8))


### Bug Fixes

* Add name_sv column to Layer admin list page ([1e8de49](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/1e8de4916f1c40fb7df92f23e309d1cdfd5abbb2))
* IconDrawingConfig constraints where not working ([12d8356](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/12d835611fe9f19fb5fb65920973b0989defe843))
* Map-view line drawing between plan and real features was very slow ([f1c348b](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/f1c348b4532ee296575bcf2c192eee4c8758c9e5))
* Map-view used device_type.code instead of device_type.icon ([b0be054](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/b0be054cc5eaeb59670a86e9110c3165e82bcebd))
* Move decision_date from metadata section to General information section ([2dc35c6](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/2dc35c64ce0516a586263596051d3d1f97b241f7))
* Plan and real difference line dissappeared every time when FeatureInfo was opened. ([fe28898](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/fe288986881ae5e62d2104f4666cabee4057cda2))

## [1.15.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.14.0...city-infrastructure-platform-v1.15.0) (2025-05-21)


### Features

* Add overviewmap for map-view ([b7eb5ea](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/b7eb5eadbe0003e4b1a45a0c29095d00dcf4de6b))
* Add support for swedish in map-view ([12939bb](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/12939bb6a8871e01f9e8fb3422348c2904944369))
* Get featureinfo titles from layer config ([3d4bf44](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/3d4bf44f3ceba02acde86a404c885483dd4b8911))
* Support for drawing trafficsign icons also as pngs ([a6d6777](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/a6d6777dbb1322b72585b6d277f6944ca3a644cb))
* Use black as area border stroke color ([831a984](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/831a984378c74c90b7940dc5c052c3056349bbb8))


### Bug Fixes

* Non clustered features edit link was not working in FeatureInfo component ([109901c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/109901c2c73a88fd124f25cc1e4a0a1a98ca3248))

## [1.14.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.13.0...city-infrastructure-platform-v1.14.0) (2025-05-12)


### Features

* Slighly better workaround for ChunkedQuerySetIterator._restore_caches overwrite ([6544558](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/6544558531ef3ad92a1a3c4a96ce942774b94d27))
* Support to  all geometry types in map-view ([d43f916](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d43f916fa82ecb73f36b3175531d2226894f0e2e))


### Bug Fixes

* Do not use plan real difference features for featureinfo popup ([f130d87](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/f130d8739c10f286827c0542d83c5a4732344332))

## [1.13.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.12.0...city-infrastructure-platform-v1.13.0) (2025-04-28)


### Features

* Add support to map feature edit links ([1ac8766](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/1ac8766f279140b0e94082eb8a861cb2ba94d75c))
* Update django-admin-confirmation ([37c9859](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/37c98592219cca115baf9214648a8fe0fe1606a8))

## [1.12.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.11.0...city-infrastructure-platform-v1.12.0) (2025-04-14)


### Features

* Add source_name to TrafficSignPlanAdmin ([18e5716](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/18e57165be414925e8493ef0295cd7da4a1408c3))
* Additional_sign_plan.parent is now nonnullable ([9f56002](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/9f56002291508f861d5b2b1fad645623d7526cc3))
* Move some js package from devdeps to real deps so builds actually work ([1f88bec](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/1f88beca92c411bffc9bc1bbc45fb5ec18c59238))
* Update django-gisserver version to 1.5.0 ([20cb850](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/20cb850604c884671b9a6398c25b10595257db46))
* Update libraries for map-view ([c4f1fc6](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/c4f1fc68b25ac616567df3f06b91bdc19c1847f0))
* Update ol.js version from 6 to 10 ([8db93b4](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/8db93b4ac13b9d3add11a9c894cf0ccc1a0c1d4c))
* Use Vite instead of Create React App ([0c17af9](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/0c17af9c1afaff24447fd892441c33f4fdcefd79))
* Workaround for gisserver not supporting all field types ([a3406d1](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/a3406d1e955b98faabd87a62da6ce7f3adf5273d))


### Bug Fixes

* FeatureIndex was not reseted when cliking anohter feature from the map without closing previous feature ([3892e5a](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/3892e5a017794cec9fee196150591f429f15d455))
* Mapview crash when feature has content_s ([e61e65a](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/e61e65a6384ba4172083a5472ba96c47243d4a9e))

## [1.11.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.10.0...city-infrastructure-platform-v1.11.0) (2025-03-24)


### Features

* Update AdditionalSignReal additional_information and update content_s if possible ([7928821](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/79288218d2e460db592b82488a09c51d459ba2c9))
* Update missing (mostly swedish) translations ([d62fbbc](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d62fbbcff217303a61ca779b2c82d1d1026f2cad))


### Bug Fixes

* Update django-helusers version ([b85d848](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/b85d84869fb5e40b72510948556346db4a3299d1))

## [1.10.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.9.0...city-infrastructure-platform-v1.10.0) (2025-03-10)


### Features

* Add confirmation if location of a Plan is manually changed and derive location is on ([12ad156](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/12ad1569e7665a30498c7ad0413549dbd86b34f4))
* Capture log message from django libgeos and show that as location_ewkt validation error message. ([7ed0cbd](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/7ed0cbd623b7b80633022184fd05c0cefb5f6ed7))


### Bug Fixes

* Changing derive_location to false without changing location or location_ekwt caused unhandled exception ([71ef64f](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/71ef64f8a043de949f86c06553f6c080fb7a53c3))
* Derive location confirmation not asked when it should be ([1b505fb](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/1b505fb0f12effe7173ad6b0f64d843616e43cab))
* Validator for location_ewkt form field. ([516a064](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/516a06463f10a1f1555b835e487c2c87e3ab52bd))

## [1.9.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.8.0...city-infrastructure-platform-v1.9.0) (2025-02-26)


### Features

* Add mount plan and real map layer rendering ([168090c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/168090c21627dbc5b8a2c249105a3de9157840f9))
* Add some new translation to mapview ([f5f8af6](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/f5f8af6af976dbc246b4f3c3044e5c3d4f5ff160))
* Centroid location rendering to WFS json output ([06e353f](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/06e353faa1139064213291a3b2dd6d3f4fd1c891))

## [1.8.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.7.0...city-infrastructure-platform-v1.8.0) (2025-02-18)


### Features

* Add mount_real_id field to TrafficSignReal and AdditionalSignReal WFS api ([22480a6](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/22480a65d276c041fe8e6ba1c93799c9039cb761))

## [1.7.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.6.1...city-infrastructure-platform-v1.7.0) (2025-02-12)


### Features

* Add id field to most Admin model search fields ([a13d4af](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/a13d4afbfe237f04f3b41eba9756df8ab59ddf53))
* Add id field to TrafficControlDeviceType export file ([fab8a2d](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/fab8a2da54c8f30a04967448f46c8fcca0bc0d57))
* Add name field to Plan admin search ([602c70d](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/602c70d85c497c74da6a7d3fc31ff197f5877d60))
* Change Plan WFS title to Traffic Control Plan ([ba0615c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/ba0615c115b84323a4b369f3c8de52c97fe98426))


### Bug Fixes

* Location can now be cleared from admin page using location_ekwt field in models that location is nullable ([fe577ce](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/fe577ce14874a870207ae7baf6a20e86bbb3809e))

## [1.6.1](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.6.0...city-infrastructure-platform-v1.6.1) (2025-02-04)


### Bug Fixes

* Plan WFS now uses convex_hull instead of Multipolygon as geometry type ([23d89d2](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/23d89d2a72cab50c92847b3bf5f63ed5682cc580))

## [1.6.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.5.0...city-infrastructure-platform-v1.6.0) (2025-01-31)


### Features

* Add decision_url to Plan admin page ([1cfe8b1](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/1cfe8b1be070503864436fb7b607386a5a4f2dcd))
* Add Plan WFS feature ([b939f1b](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/b939f1bfdfb9ba691575563911ef576b0f8cd0c6))
* Add search fields to Plan admin ([98eb08a](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/98eb08a81a9c1f0dbba05d14f38dda37ac0bdfa4))
* Show location information fields one below another instead of side-by-side ([ab8b78e](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/ab8b78ea6292729df0aee616b7114c48613f0d43))

## [1.5.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.4.0...city-infrastructure-platform-v1.5.0) (2025-01-29)


### Features

* Add devicetype code and legacy code to admin search to all models that have device type ([98fa983](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/98fa98349903f083be07880dfaa9558e1c8cd02d))
* Management command for updating plan information from a csv-file ([bd56a0a](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/bd56a0ab15c196a01fee6d87408576eacfbeb88d))
* Unregister social_auth user admin view ([d960319](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d9603195fd8cd909cf7d38def71f0981b520eab5))

## [1.4.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.3.0...city-infrastructure-platform-v1.4.0) (2025-01-14)


### Features

* Add all possible content_s fields to template export for additional sign plans and reals ([1305079](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/1305079e7906ddf6bde90416de819ad287a50718))
* Register User model to auditlog ([07fc4aa](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/07fc4aa41349b1ebe180267aadf109758e5aeb0a))


### Bug Fixes

* Auditlog entries are now create also for user invidual permission updates ([77bef68](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/77bef6887477e10df5fcf2d93c74cddaa2486547))

## [1.3.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.2.0...city-infrastructure-platform-v1.3.0) (2024-12-20)


### Features

* Centroid WFS Feature for mount plans and reals instead of only for portal types. ([650a0d6](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/650a0d69b588990291112f893dd58c36975bc1ad))
* WFS Feature for mountplans and mountreals that uses centroid as instead of real location ([f5baeda](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/f5baedadd976edc0b5ee092d08ca34dc065b47c3))


### Bug Fixes

* Add missing internationalization support for mount centroid titles ([84a2eb6](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/84a2eb612617e0ba7b2921399a7c3ebf4f4f952f))
* Many fixes related to location handling in admin forms ([5b09d92](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/5b09d92b8d5736582a57cd2d79b772c563b28db8))

## [1.2.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.1.0...city-infrastructure-platform-v1.2.0) (2024-12-16)


### Features

* Add additional_information to users ([dd8cb38](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/dd8cb3812e46be86de899cf6ac62857409bd55f8))
* Allowed location is now bound with Helsinki city limits ([a44ba1e](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/a44ba1e84a571228861749eec0ec3e9647abea8b))
* API maximum result per page configuration ([0ff52f9](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/0ff52f939ce8c44e5bac174ff5067101362a90bf))
* Make source_name and source_id editable in all admin models where they exist ([ff0c74d](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/ff0c74d9cf02f1d8b00327f9477b93c02447b4c3))
* Use map widget for all models that have a location ([25acfbe](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/25acfbe657c45296f0691aa238cfc7bb4b008b19))


### Bug Fixes

* Use same values for lane_number as digiroad ([6e753c5](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/6e753c5de98cb8d99ca0256e4634094d3920285f))
* Xy coordinate swap now done for all geometry types for WFS gml api ([064522d](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/064522dfc22f9eea24441790cd8e25cdf32adef4))

## [1.1.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v1.0.0...city-infrastructure-platform-v1.1.0) (2024-11-29)


### Features

* Add source_name and source_id to import-export resources where applicable ([ca28781](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/ca28781ee8a61bdc3e1303f9c553735611061038))
* List additional signs right after trafficsign in embed view ([c2a1a7f](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/c2a1a7f08cc875f9edcc44780cb3df280783d1d7))


### Bug Fixes

* Add missing internalization and finnish translation for No additional signs ([6f723cf](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/6f723cf42a671a1911f7a6286227dbfa0371b0ba))
* Do not allowd geometries outside given SRID ([e1794ac](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/e1794ac026f52db688ca2a2d3fe9c39092ae8741))

## [1.0.0](https://github.com/City-of-Helsinki/city-infrastructure-platform/compare/city-infrastructure-platform-v0.1.0...city-infrastructure-platform-v1.0.0) (2024-11-12)


### ⚠ BREAKING CHANGES

* change AdditionalSignReal parent field to be non-nullable

### Features

* Add links to privacy policies ([f64f4a8](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/f64f4a815d052a8464e1e0fe33adc98e54264dbd))
* Add MountReal and MountPlans to WFS API ([79dfaf6](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/79dfaf6cf032362d0e770fa65f68f14176280eda))
* Add parent_id and additional_information fields to AdditionalSign and Plan WFS ([3ced611](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/3ced611555f9b898a9a39d21608813de23aa2808))
* Add virus scan and file type check to file uploads via REST API ([d781a4a](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d781a4a3527920c14e34c62899242b72db86294a))
* Change AdditionalSignReal parent field to be non-nullable ([5f1da21](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/5f1da21e2c02b1f73389582e1cc22d5f2dd012ab))
* Limit unsuccessful login attemps ([490488c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/490488cf8b63e7c8dc0d3b2cf4c94d2875bfa4b8))
* Restrict filetypes that can be uploaded ([42e5277](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/42e5277b9e667487bc7dbe53a0242d0ec14e8bb5))
* Show enum name instead of value in WFS API ([da45376](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/da4537657982ac17059da0bf170a694f301f8a75))


### Bug Fixes

* AD login fails if session cookie samesite setting is set to Strict, change back to Lax ([d50c875](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d50c875e160557e4b68826a691232bdad81710dd))
* Add english for privacy policy, link goes to finnish pdf ([039bd86](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/039bd8607f52003f2766111e7da4b88fde19eb61))
* Base information was not taken into export nor in the template ([0fbe7e6](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/0fbe7e6329cdbb37ea262b3eed3408a07484af56))
* Data protection policy link finetuning ([62db1e7](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/62db1e7b4bb09a856da846a2ebb6baeb72f0ade6))
* English link pointed to swedish pdf file instead of finnish ([b59729a](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/b59729a217a47452cc0d77a1c758b9bf7424ba7b))
* Set more strict cookie policies ([337a9ea](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/337a9eafce486996057fca6f53c5eccd369faad6))
* Try to get actual client ip for login attempt limitation ([d8be07e](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/d8be07e540d57d244a18d66bf16a462324f40f43))

## 0.1.0 (2024-10-25)


### Bug Fixes

* Add decision_date to PlanAdmin ([231e50c](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/231e50cba92029e76b7d9b6a440903abf90b8f9a))
* Use master branch instead of main ([9b6e8bb](https://github.com/City-of-Helsinki/city-infrastructure-platform/commit/9b6e8bb4252abf524cb97be1c4d629fa0c755905))

## Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
