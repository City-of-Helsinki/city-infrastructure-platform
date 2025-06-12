# Changelog

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
