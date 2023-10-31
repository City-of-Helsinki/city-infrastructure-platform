const createStructuredContentWidget = async (name, options) => {
  const { deviceTypeName, deviceTypeEndpoint } = options;

  const editorContainerId = name + "_editor";
  const editorContainer = document.getElementById(editorContainerId);

  const valueContainerId = "id_" + name;
  const valueContainer = document.getElementById(valueContainerId);

  const deviceTypeWidgetId = "id_" + deviceTypeName;
  const deviceTypeWidget = document.getElementById(deviceTypeWidgetId);

  const missingContentId = "id_missing_content";
  const missingContent = document.getElementById(missingContentId);

  const refreshEditorEventHandler = () => {
    refreshEditor(
      editorContainer,
      valueContainer,
      deviceTypeWidget,
      deviceTypeEndpoint,
      missingContent
    );
  };

  deviceTypeWidget.addEventListener("change", refreshEditorEventHandler);
  missingContent.addEventListener("change", refreshEditorEventHandler);
  refreshEditorEventHandler();
};

const getDeviceTypeContentSchema = async (deviceTypeId, deviceTypeEndpoint) => {
  const deviceTypeUrl = deviceTypeEndpoint.replace("__id__", deviceTypeId);

  const response = await fetch(deviceTypeUrl, {
    method: "GET",
    cache: "no-cache",
    headers: {
      accept: "application/json",
    },
  });

  if (response.ok) {
    const data = await response.json();
    return data.content_schema;
  } else {
    console.error(
      `Error while fetching "${deviceTypeUrl}":\n${response.statusText}`
    );
  }
};

const getDocumentLanguage = () => {
  return document.documentElement.lang;
};

const translateProperty = (key) => {
  const lang = getDocumentLanguage();

  return lang + key;
};

const refreshEditor = async (
  editorContainer,
  valueContainer,
  deviceTypeWidget,
  deviceTypeEndpoint,
  missingContent
) => {
  editorContainer.replaceChildren();

  const deviceTypeId = deviceTypeWidget.value;

  const contentSchema = await getDeviceTypeContentSchema(
    deviceTypeId,
    deviceTypeEndpoint
  );

  if (contentSchema && !missingContent.checked) {
    const editorOptions = {
      schema: contentSchema,
      theme: "html",
      disable_collapse: true,
      disable_edit_json: true,
      disable_properties: true,
    };

    const editor = new JSONEditor(editorContainer, editorOptions);

    const lang = getDocumentLanguage();
    editor.translateProperty = (key) => {
      if (contentSchema.propertiesTitles) {
        return contentSchema.propertiesTitles[lang][key] || key;
      } else {
        return key;
      }
    };

    editor.on("ready", () => {
      const content = JSON.parse(valueContainer.value);
      editor.setValue(content);
    });

    editor.on("change", () => {
      editor.validate();

      const jsonValue = editor.getValue();
      valueContainer.value = JSON.stringify(jsonValue);
    });
  } else {
    // If there is no schema, remove the value and don't show the editor
    valueContainer.value = JSON.stringify(null);
  }
};
