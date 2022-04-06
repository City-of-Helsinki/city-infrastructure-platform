(function($) {
  $(document).ready(function() {
    var $actionsSelect, $formatsElement;
    $actionsSelect = $('#changelist-form select[name="action"]');
    $formatsElement = $('#changelist-form select[name="file_format"]').parent();
    $exportResourcesElement = $('#changelist-form select[name="export_resource_class"]').parent();

    $actionsSelect.change(function() {
      if ($(this).val() === 'export_admin_action') {
        $formatsElement.show();
        $exportResourcesElement.show();
      } else {
        $formatsElement.hide();
        $exportResourcesElement.hide();
      }
    });
    $actionsSelect.change();
  });
})(django.jQuery);
