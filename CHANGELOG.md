# Changelog

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
