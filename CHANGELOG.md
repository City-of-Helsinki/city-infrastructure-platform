# Changelog

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
