# Changelog

## [v1.8.3](https://github.com/babybuddy/babybuddy/tree/v1.8.3) (2021-08-27)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.8.2...v1.8.3)

**Implemented enhancements:**

- Timeline view: Activities should include their notes \(or at least mark activities that have notes\) [\#272](https://github.com/babybuddy/babybuddy/issues/272)
- Improve cross-midnight timeline view [\#270](https://github.com/babybuddy/babybuddy/issues/270)
- Timeline: For feedings, show time-since-feeding-before [\#266](https://github.com/babybuddy/babybuddy/issues/266)
- Start / finish times are treated as inclusive-at-both-ends ranges rather than standard half-open ranges [\#263](https://github.com/babybuddy/babybuddy/issues/263)
- add SECURE\_PROXY\_SSL\_HEADER env arg option [\#285](https://github.com/babybuddy/babybuddy/pull/285) ([jcgoette](https://github.com/jcgoette))

**Fixed bugs:**

- KeyError when generating graph for sleep pattern [\#293](https://github.com/babybuddy/babybuddy/issues/293)
- Graph x-axis date labels should not show times, only dates. [\#288](https://github.com/babybuddy/babybuddy/issues/288)
- Sleep graph uses 12h format when 24h is enabled. [\#287](https://github.com/babybuddy/babybuddy/issues/287)
- Mobile submit button prevents date selection in some circumstances [\#265](https://github.com/babybuddy/babybuddy/issues/265)

**Merged pull requests:**

- add Docker admin activity example [\#282](https://github.com/babybuddy/babybuddy/pull/282) ([jcgoette](https://github.com/jcgoette))
- Add date-nav to bottom [\#281](https://github.com/babybuddy/babybuddy/pull/281) ([lutzky](https://github.com/lutzky))
- Show notes in timeline [\#280](https://github.com/babybuddy/babybuddy/pull/280) ([lutzky](https://github.com/lutzky))
- Add "time since previous feeding" [\#275](https://github.com/babybuddy/babybuddy/pull/275) ([lutzky](https://github.com/lutzky))

## [v1.8.2](https://github.com/babybuddy/babybuddy/tree/v1.8.2) (2021-08-06)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.8.1...v1.8.2)

**Fixed bugs:**

- Default SQLite DB behavior broken in v1.8.1 [\#279](https://github.com/babybuddy/babybuddy/issues/279)

## [v1.8.1](https://github.com/babybuddy/babybuddy/tree/v1.8.1) (2021-08-06)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.8.0...v1.8.1)

**Fixed bugs:**

- List time stamps localization bug [\#276](https://github.com/babybuddy/babybuddy/issues/276)
- v1.8 shorter timestamps using UTC time [\#274](https://github.com/babybuddy/babybuddy/issues/274)
- docker configured with postgres uses sqlite3 [\#273](https://github.com/babybuddy/babybuddy/issues/273)

## [v1.8.0](https://github.com/babybuddy/babybuddy/tree/v1.8.0) (2021-08-05)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.7.0...v1.8.0)

**Implemented enhancements:**

- Move Time column to be first in list view [\#232](https://github.com/babybuddy/babybuddy/issues/232)
- Don't hide Submit button below optional fields [\#231](https://github.com/babybuddy/babybuddy/issues/231)
- Dashboard: Move "Last Diaper Change" to near-top [\#230](https://github.com/babybuddy/babybuddy/issues/230)
- Use shorter timestamp formats in list view [\#237](https://github.com/babybuddy/babybuddy/issues/237)
- Move Color and Amount columns to far right in list view [\#236](https://github.com/babybuddy/babybuddy/issues/236)
- Unify "wet" and "solid" columns to a quad-state in list view [\#235](https://github.com/babybuddy/babybuddy/issues/235)
- Links from dashboard [\#234](https://github.com/babybuddy/babybuddy/issues/234)
- Hide Child column if only one child is shown [\#233](https://github.com/babybuddy/babybuddy/issues/233)
- Feature/UI Request: Only require a single time for feedings [\#192](https://github.com/babybuddy/babybuddy/issues/192)
- Dashboard: Auto-refresh even if focus is supported [\#255](https://github.com/babybuddy/babybuddy/pull/255) ([lutzky](https://github.com/lutzky))
- Make form submit full width fixed [\#254](https://github.com/babybuddy/babybuddy/pull/254) ([cdubz](https://github.com/cdubz))
- Brighten blue and cyan colors [\#251](https://github.com/babybuddy/babybuddy/pull/251) ([lutzky](https://github.com/lutzky))

**Fixed bugs:**

- Heroku approaching row limit [\#219](https://github.com/babybuddy/babybuddy/issues/219)

**Closed issues:**

- Force periodic refresh for always-on-devices [\#253](https://github.com/babybuddy/babybuddy/issues/253)
- Upgrade from 1.41 [\#252](https://github.com/babybuddy/babybuddy/issues/252)

**Merged pull requests:**

- Ignore files in static for repository language [\#269](https://github.com/babybuddy/babybuddy/pull/269) ([lutzky](https://github.com/lutzky))
- Add links from dashboard [\#268](https://github.com/babybuddy/babybuddy/pull/268) ([lutzky](https://github.com/lutzky))
- Move Actions column to the far left [\#267](https://github.com/babybuddy/babybuddy/pull/267) ([lutzky](https://github.com/lutzky))
- Unify "wet" and "solid" columns [\#264](https://github.com/babybuddy/babybuddy/pull/264) ([lutzky](https://github.com/lutzky))
- Hide child column if only one child is shown [\#262](https://github.com/babybuddy/babybuddy/pull/262) ([lutzky](https://github.com/lutzky))
- Consider last-feeding-method as empty if never-changing [\#261](https://github.com/babybuddy/babybuddy/pull/261) ([lutzky](https://github.com/lutzky))
- Use short datetime string for lists [\#260](https://github.com/babybuddy/babybuddy/pull/260) ([cdubz](https://github.com/cdubz))
- Provide example config for secure cookies [\#259](https://github.com/babybuddy/babybuddy/pull/259) ([cdubz](https://github.com/cdubz))
- Move Time column to be first in list view [\#250](https://github.com/babybuddy/babybuddy/pull/250) ([lutzky](https://github.com/lutzky))
- Dashboard: Move all "last" cards to top [\#248](https://github.com/babybuddy/babybuddy/pull/248) ([lutzky](https://github.com/lutzky))
- Show duration in timeline [\#247](https://github.com/babybuddy/babybuddy/pull/247) ([lutzky](https://github.com/lutzky))

## [v1.7.0](https://github.com/babybuddy/babybuddy/tree/v1.7.0) (2021-07-08)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.6.0...v1.7.0)

**Implemented enhancements:**

- Potential security issue  [\#226](https://github.com/babybuddy/babybuddy/issues/226)

**Fixed bugs:**

- `pipenv install` fails because of psycopg2 [\#238](https://github.com/babybuddy/babybuddy/issues/238)
- Disable autocomplete for date and time fields [\#224](https://github.com/babybuddy/babybuddy/issues/224)

**Closed issues:**

- iOS Shortcut: "Authentication credentials were not provided" [\#222](https://github.com/babybuddy/babybuddy/issues/222)
- Move from Travis CI to GitHub Actions or something else [\#214](https://github.com/babybuddy/babybuddy/issues/214)
- Child slug may become empty [\#205](https://github.com/babybuddy/babybuddy/issues/205)
- Unable to run on docker ARM64 [\#199](https://github.com/babybuddy/babybuddy/issues/199)
- `WORKER TIMEOUT` on Docker 20.x [\#227](https://github.com/babybuddy/babybuddy/issues/227)

**Merged pull requests:**

- Add `libpq-dev` to instructions [\#242](https://github.com/babybuddy/babybuddy/pull/242) ([lutzky](https://github.com/lutzky))
- Make docker-compose examples unicorn-appropriate [\#228](https://github.com/babybuddy/babybuddy/pull/228) ([lutzky](https://github.com/lutzky))
- Replace Travis with GitHub Actions [\#216](https://github.com/babybuddy/babybuddy/pull/216) ([cdubz](https://github.com/cdubz))
- Timeline: Add edit links [\#246](https://github.com/babybuddy/babybuddy/pull/246) ([lutzky](https://github.com/lutzky))
- Update deployment documentation [\#245](https://github.com/babybuddy/babybuddy/pull/245) ([cdubz](https://github.com/cdubz))
- Clarify "no events" on timeline [\#244](https://github.com/babybuddy/babybuddy/pull/244) ([lutzky](https://github.com/lutzky))
- Timeline: Show diaper change details [\#243](https://github.com/babybuddy/babybuddy/pull/243) ([lutzky](https://github.com/lutzky))
- Reverted tempus dominus to the previous version to fix an issue with marking fields as read only [\#241](https://github.com/babybuddy/babybuddy/pull/241) ([ntrecina](https://github.com/ntrecina))
- Show feeding amount on timeline [\#240](https://github.com/babybuddy/babybuddy/pull/240) ([lutzky](https://github.com/lutzky))
- Show absolute last times in dashboard [\#239](https://github.com/babybuddy/babybuddy/pull/239) ([lutzky](https://github.com/lutzky))
- Update dutch translation [\#225](https://github.com/babybuddy/babybuddy/pull/225) ([svenvdmeer](https://github.com/svenvdmeer))
- Feedings [\#223](https://github.com/babybuddy/babybuddy/pull/223) ([jcgoette](https://github.com/jcgoette))
- update post: sections [\#221](https://github.com/babybuddy/babybuddy/pull/221) ([jcgoette](https://github.com/jcgoette))
- change ADD to COPY [\#220](https://github.com/babybuddy/babybuddy/pull/220) ([jcgoette](https://github.com/jcgoette))
- Dashboard: Hide old data [\#215](https://github.com/babybuddy/babybuddy/pull/215) ([BenjaminHae](https://github.com/BenjaminHae))

## [v1.6.0](https://github.com/babybuddy/babybuddy/tree/v1.6.0) (2021-05-14)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.5.1...v1.6.0)

**Fixed bugs:**

- unsupported format character in "duration\_string" \(i18n problem, german language\) [\#208](https://github.com/babybuddy/babybuddy/issues/208)
- Test `test_user_settings_language` fails in CI consistently but does not fail CI [\#203](https://github.com/babybuddy/babybuddy/issues/203)
- Sleep Pattern Error [\#198](https://github.com/babybuddy/babybuddy/issues/198)

**Closed issues:**

- Docker-compose settings being ignored [\#204](https://github.com/babybuddy/babybuddy/issues/204)

**Merged pull requests:**

- add option for hiding empty dashboard cards \(3\) [\#213](https://github.com/babybuddy/babybuddy/pull/213) ([BenjaminHae](https://github.com/BenjaminHae))
- Fixes another issue with translation \(de\) [\#212](https://github.com/babybuddy/babybuddy/pull/212) ([BenjaminHae](https://github.com/BenjaminHae))
- fix translation format strings [\#209](https://github.com/babybuddy/babybuddy/pull/209) ([BenjaminHae](https://github.com/BenjaminHae))
- fixes translation \(de\) [\#210](https://github.com/babybuddy/babybuddy/pull/210) ([BenjaminHae](https://github.com/BenjaminHae))
- child slugs: Require non-blank, preserve unicode letters [\#206](https://github.com/babybuddy/babybuddy/pull/206) ([cben](https://github.com/cben))
- Add solid food option to feeding types [\#201](https://github.com/babybuddy/babybuddy/pull/201) ([0x4161726f6e](https://github.com/0x4161726f6e))

## [v1.5.1](https://github.com/babybuddy/babybuddy/tree/v1.5.1) (2021-02-25)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.5.0...v1.5.1)

**Fixed bugs:**

- Translations are inconsistent on Docker Deployment of v 1.5 [\#197](https://github.com/babybuddy/babybuddy/issues/197)

**Closed issues:**

- iFrame Support [\#184](https://github.com/babybuddy/babybuddy/issues/184)
- Using Minio and an S3 endpoint via the AWS\_S3\_ENDPOINT\_URL setting [\#183](https://github.com/babybuddy/babybuddy/issues/183)
- Improve manual install documentation step 4 [\#194](https://github.com/babybuddy/babybuddy/issues/194)

**Merged pull requests:**

- Remove leading space in code blocks [\#195](https://github.com/babybuddy/babybuddy/pull/195) ([jcgoette](https://github.com/jcgoette))
- Add Notes to Applicable APIs [\#193](https://github.com/babybuddy/babybuddy/pull/193) ([jcgoette](https://github.com/jcgoette))
- Boolean field labels are no longer clickable [\#188](https://github.com/babybuddy/babybuddy/pull/188) ([ntrecina](https://github.com/ntrecina))

## [v1.5.0](https://github.com/babybuddy/babybuddy/tree/v1.5.0) (2021-01-06)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.4.1...v1.5.0)

**Implemented enhancements:**

- Add tracking for height [\#105](https://github.com/babybuddy/babybuddy/issues/105)
- Feature Request: Media Tracking [\#87](https://github.com/babybuddy/babybuddy/issues/87)
- Feature Request: Development Milestones [\#86](https://github.com/babybuddy/babybuddy/issues/86)
- Postgres password concern [\#180](https://github.com/babybuddy/babybuddy/issues/180)
- Store birthday as timestamp with time zone [\#167](https://github.com/babybuddy/babybuddy/issues/167)
- Adding via Portainer [\#165](https://github.com/babybuddy/babybuddy/issues/165)
- Allow to set/change the date/time of notes [\#151](https://github.com/babybuddy/babybuddy/issues/151)

**Fixed bugs:**

- Last Feeding - 0 Days [\#181](https://github.com/babybuddy/babybuddy/issues/181)
- Travis running all tests with Python 3.8 [\#158](https://github.com/babybuddy/babybuddy/issues/158)
- Unable to run `gulp migrate` locally as database path does not exist [\#156](https://github.com/babybuddy/babybuddy/issues/156)

**Closed issues:**

- Recommend Backup Solution [\#164](https://github.com/babybuddy/babybuddy/issues/164)
- Integration with HA [\#163](https://github.com/babybuddy/babybuddy/issues/163)
- Start page showing "Welcome to nginx!" [\#157](https://github.com/babybuddy/babybuddy/issues/157)
- pre-filled date/time [\#91](https://github.com/babybuddy/babybuddy/issues/91)
- Use of datetime.date.fromisoformat breaks Python 3.6 compatability [\#170](https://github.com/babybuddy/babybuddy/issues/170)
- POEditor translations not reflected in codebase [\#168](https://github.com/babybuddy/babybuddy/issues/168)
- Refactor Sleep pattern graph to not need pandas/numpy [\#116](https://github.com/babybuddy/babybuddy/issues/116)

**Merged pull requests:**

- Allow for custom PostgreSQL Deployments [\#182](https://github.com/babybuddy/babybuddy/pull/182) ([Zutart](https://github.com/Zutart))
- Updates to docker compose files for Portainer compatibility [\#179](https://github.com/babybuddy/babybuddy/pull/179) ([phidauex](https://github.com/phidauex))
- Refactor to remove pandas dependency [\#177](https://github.com/babybuddy/babybuddy/pull/177) ([cdubz](https://github.com/cdubz))
- Update README.md [\#175](https://github.com/babybuddy/babybuddy/pull/175) ([jcgoette](https://github.com/jcgoette))
- Use correct Python versions in Travis CI [\#169](https://github.com/babybuddy/babybuddy/pull/169) ([cdubz](https://github.com/cdubz))
- German spelling corrections [\#160](https://github.com/babybuddy/babybuddy/pull/160) ([dettmering](https://github.com/dettmering))
- Fixed duplicate data/form-submit from double click [\#173](https://github.com/babybuddy/babybuddy/pull/173) ([ABOTlegacy](https://github.com/ABOTlegacy))
- Add Finnish language [\#152](https://github.com/babybuddy/babybuddy/pull/152) ([haiksu](https://github.com/haiksu))

## [v1.4.1](https://github.com/babybuddy/babybuddy/tree/v1.4.1) (2020-07-27)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.4.0...v1.4.1)

**Implemented enhancements:**

- Using 24H format for time [\#148](https://github.com/babybuddy/babybuddy/issues/148)
- \[Feature Request\] API Endpoints to end timers and associate that timer with a task [\#131](https://github.com/babybuddy/babybuddy/issues/131)

**Fixed bugs:**

- Deploy to Heroku Fails on Boto [\#146](https://github.com/babybuddy/babybuddy/issues/146)
- "Today's Naps" card no longer has data [\#136](https://github.com/babybuddy/babybuddy/issues/136)

**Closed issues:**

- docker-compose example needs rework [\#141](https://github.com/babybuddy/babybuddy/issues/141)
- server error 500 after initial login [\#140](https://github.com/babybuddy/babybuddy/issues/140)
- Feature request: Allow hiding the "Last Feeding Method" card [\#139](https://github.com/babybuddy/babybuddy/issues/139)
- Docker data problems [\#129](https://github.com/babybuddy/babybuddy/issues/129)
- Allow activity without ending datetime, to be filled in later [\#92](https://github.com/babybuddy/babybuddy/issues/92)
- Add importable API examples JSON file [\#147](https://github.com/babybuddy/babybuddy/issues/147)
- Docker instance using Sqlite [\#145](https://github.com/babybuddy/babybuddy/issues/145)
- Set user automatically on Timer via API [\#134](https://github.com/babybuddy/babybuddy/issues/134)
- Extend session timeout [\#130](https://github.com/babybuddy/babybuddy/issues/130)
- Auto select "bottle" method with "formula" type [\#127](https://github.com/babybuddy/babybuddy/issues/127)
- Add PATCH support to API [\#126](https://github.com/babybuddy/babybuddy/issues/126)

**Merged pull requests:**

- Add support for 24 hour time override \(\#148\) [\#150](https://github.com/babybuddy/babybuddy/pull/150) ([cdubz](https://github.com/cdubz))
- Add a "Today's Feeding" card [\#149](https://github.com/babybuddy/babybuddy/pull/149) ([JeanFred](https://github.com/JeanFred))
- Ensure date passed to nap filter is localtime. [\#144](https://github.com/babybuddy/babybuddy/pull/144) ([phardy](https://github.com/phardy))
- Periodic session expiry update to prevent timeouts [\#143](https://github.com/babybuddy/babybuddy/pull/143) ([phardy](https://github.com/phardy))
- Auto select "bottle" method for formula and fortified milk types [\#138](https://github.com/babybuddy/babybuddy/pull/138) ([phardy](https://github.com/phardy))
- add enhanced feedings statistics [\#135](https://github.com/babybuddy/babybuddy/pull/135) ([BenjaminHae](https://github.com/BenjaminHae))
- \[WIP\] Update serializers to accept a "timer" argument [\#133](https://github.com/babybuddy/babybuddy/pull/133) ([cdubz](https://github.com/cdubz))
- Add API PATCH and DELETE methods [\#132](https://github.com/babybuddy/babybuddy/pull/132) ([cdubz](https://github.com/cdubz))
- Rework docker example [\#142](https://github.com/babybuddy/babybuddy/pull/142) ([MaximilianKindshofer](https://github.com/MaximilianKindshofer))

## [v1.4.0](https://github.com/babybuddy/babybuddy/tree/v1.4.0) (2020-02-19)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.3.4...v1.4.0)

**Implemented enhancements:**

- Add additional feeding methods to "Last Feeding Method" card [\#117](https://github.com/babybuddy/babybuddy/issues/117)
- Simple notes textarea for changes and feedings [\#89](https://github.com/babybuddy/babybuddy/issues/89)

**Closed issues:**

- Error: DoesNotExist at /feedings/add/ [\#114](https://github.com/babybuddy/babybuddy/issues/114)
- Get timezone from client [\#95](https://github.com/babybuddy/babybuddy/issues/95)
- Allow application time zone to be set from UI [\#113](https://github.com/babybuddy/babybuddy/issues/113)
- Improve Plotly output handling for reports [\#69](https://github.com/babybuddy/babybuddy/issues/69)
- Add ability to export/import data [\#35](https://github.com/babybuddy/babybuddy/issues/35)

**Merged pull requests:**

- Add import/export support [\#122](https://github.com/babybuddy/babybuddy/pull/122) ([cdubz](https://github.com/cdubz))
- Add ability to record notes on most entry types [\#121](https://github.com/babybuddy/babybuddy/pull/121) ([cdubz](https://github.com/cdubz))
- Add last three methods to Last Feeding Method card [\#120](https://github.com/babybuddy/babybuddy/pull/120) ([cdubz](https://github.com/cdubz))
- Remove exception handling for Plotly output \(\#69\) [\#119](https://github.com/babybuddy/babybuddy/pull/119) ([cdubz](https://github.com/cdubz))
- Allow application time zone to be set from UI [\#118](https://github.com/babybuddy/babybuddy/pull/118) ([cdubz](https://github.com/cdubz))

## [v1.3.4](https://github.com/babybuddy/babybuddy/tree/v1.3.4) (2020-02-09)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.3.3...v1.3.4)

## [v1.3.3](https://github.com/babybuddy/babybuddy/tree/v1.3.3) (2020-02-08)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.3.2...v1.3.3)

## [v1.3.2](https://github.com/babybuddy/babybuddy/tree/v1.3.2) (2020-02-07)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.3.1...v1.3.2)

## [v1.3.1](https://github.com/babybuddy/babybuddy/tree/v1.3.1) (2020-02-07)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.3.0...v1.3.1)

**Implemented enhancements:**

- Add ability to delete all inactive Timers [\#108](https://github.com/babybuddy/babybuddy/issues/108)

**Closed issues:**

- Update documentation for new Docker Hub repo [\#112](https://github.com/babybuddy/babybuddy/issues/112)
- Test case test\_timer\_stop\_on\_save fails occasionally [\#111](https://github.com/babybuddy/babybuddy/issues/111)
- Use docker-compose's environment instead of docker.env file [\#110](https://github.com/babybuddy/babybuddy/issues/110)
- Implement pull-to-refresh [\#107](https://github.com/babybuddy/babybuddy/issues/107)
- Docker Compose configuration prevents tagged image updates [\#106](https://github.com/babybuddy/babybuddy/issues/106)

## [v1.3.0](https://github.com/babybuddy/babybuddy/tree/v1.3.0) (2020-01-31)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.2.4...v1.3.0)

**Implemented enhancements:**

- Add a "Now" button to input the current date and time [\#99](https://github.com/babybuddy/babybuddy/issues/99)
- Allow AM/PM instead of military time [\#93](https://github.com/babybuddy/babybuddy/issues/93)
- FR: Diaper change volume [\#77](https://github.com/babybuddy/babybuddy/issues/77)
- Timezone [\#50](https://github.com/babybuddy/babybuddy/issues/50)

**Fixed bugs:**

- Time conversion issues in Timers [\#90](https://github.com/babybuddy/babybuddy/issues/90)
- Time numbers in calendar pop out wrong color [\#96](https://github.com/babybuddy/babybuddy/issues/96)

**Closed issues:**

- Login username case sensitivity [\#98](https://github.com/babybuddy/babybuddy/issues/98)
- Feature Request: Customizable Dashboard [\#88](https://github.com/babybuddy/babybuddy/issues/88)
- Add `updatestatic` management command [\#102](https://github.com/babybuddy/babybuddy/issues/102)
- Improve datetime picker widget [\#101](https://github.com/babybuddy/babybuddy/issues/101)
- Add optional Child relationship to Timer [\#100](https://github.com/babybuddy/babybuddy/issues/100)

**Merged pull requests:**

- Add optional Child relationship to Timer [\#104](https://github.com/babybuddy/babybuddy/pull/104) ([cdubz](https://github.com/cdubz))
- Improve datetime picker widget [\#103](https://github.com/babybuddy/babybuddy/pull/103) ([cdubz](https://github.com/cdubz))
- Update to Node 10 minimum version for development [\#97](https://github.com/babybuddy/babybuddy/pull/97) ([cdubz](https://github.com/cdubz))
- Support localized datetime strings [\#94](https://github.com/babybuddy/babybuddy/pull/94) ([cdubz](https://github.com/cdubz))

## [v1.2.4](https://github.com/babybuddy/babybuddy/tree/v1.2.4) (2020-01-04)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.2.3...v1.2.4)

**Implemented enhancements:**

- Enhancement: "Fortified breast milk" Option [\#71](https://github.com/babybuddy/babybuddy/issues/71)
- FR/Question: active timers on home dashboard [\#73](https://github.com/babybuddy/babybuddy/issues/73)
- feature request: Feeding daily input [\#68](https://github.com/babybuddy/babybuddy/issues/68)

**Fixed bugs:**

- graph.da32e0532ca2.js.gz is empty [\#75](https://github.com/babybuddy/babybuddy/issues/75)
- Some translated strings not working. [\#64](https://github.com/babybuddy/babybuddy/issues/64)

**Closed issues:**

- API questions [\#76](https://github.com/babybuddy/babybuddy/issues/76)
- Module 'encodings' not found [\#67](https://github.com/babybuddy/babybuddy/issues/67)
- Pine64 Docker install fails [\#59](https://github.com/babybuddy/babybuddy/issues/59)

**Merged pull requests:**

- Spelling corrections for 'not enough information' messages [\#85](https://github.com/babybuddy/babybuddy/pull/85) ([nelsonblaha](https://github.com/nelsonblaha))
- Extend translation support [\#84](https://github.com/babybuddy/babybuddy/pull/84) ([cdubz](https://github.com/cdubz))
- Improve german tummy time translation [\#83](https://github.com/babybuddy/babybuddy/pull/83) ([irmela](https://github.com/irmela))
- Update dashboard.html [\#82](https://github.com/babybuddy/babybuddy/pull/82) ([paulcalabro](https://github.com/paulcalabro))
- A couple minor changes [\#81](https://github.com/babybuddy/babybuddy/pull/81) ([paulcalabro](https://github.com/paulcalabro))
- Time last feeding from start [\#78](https://github.com/babybuddy/babybuddy/pull/78) ([PhilRW](https://github.com/PhilRW))
- Add dashboard sort clauses: first name and id [\#74](https://github.com/babybuddy/babybuddy/pull/74) ([burkemw3](https://github.com/burkemw3))

## [v1.2.3](https://github.com/babybuddy/babybuddy/tree/v1.2.3) (2019-06-07)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.2.2...v1.2.3)

**Implemented enhancements:**

- Feature Reqest: Temperature [\#53](https://github.com/babybuddy/babybuddy/issues/53)
- Feature Reqest: Feeding; both Breasts [\#52](https://github.com/babybuddy/babybuddy/issues/52)

**Closed issues:**

- Best way to update to latest? [\#65](https://github.com/babybuddy/babybuddy/issues/65)

**Merged pull requests:**

- Added German translation \(informal, with "du"\) [\#72](https://github.com/babybuddy/babybuddy/pull/72) ([cephos](https://github.com/cephos))

## [v1.2.2](https://github.com/babybuddy/babybuddy/tree/v1.2.2) (2019-05-04)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.2.1...v1.2.2)

**Implemented enhancements:**

- Feature Reqest: Multilanguage Support [\#62](https://github.com/babybuddy/babybuddy/issues/62)
- Make Baby Buddy translatable [\#63](https://github.com/babybuddy/babybuddy/pull/63) ([cdubz](https://github.com/cdubz))

## [v1.2.1](https://github.com/babybuddy/babybuddy/tree/v1.2.1) (2019-04-10)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.2.0...v1.2.1)

**Closed issues:**

- Commit compiled assets [\#56](https://github.com/babybuddy/babybuddy/issues/56)
- Manual Installation on ARM7: ImportError: Missing required dependencies \['numpy'\] [\#55](https://github.com/babybuddy/babybuddy/issues/55)

**Merged pull requests:**

- Use pre-built docker image for compose [\#60](https://github.com/babybuddy/babybuddy/pull/60) ([sharkoz](https://github.com/sharkoz))

## [v1.2.0](https://github.com/babybuddy/babybuddy/tree/v1.2.0) (2018-11-06)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.1.0...v1.2.0)

**Closed issues:**

- Safari pinned iOS App links to Home / Permission denied [\#57](https://github.com/babybuddy/babybuddy/issues/57)
- auto reboot server on reboot [\#54](https://github.com/babybuddy/babybuddy/issues/54)
- users not able to login [\#49](https://github.com/babybuddy/babybuddy/issues/49)
- configure nginx [\#47](https://github.com/babybuddy/babybuddy/issues/47)
- Persistent Data - Docker [\#46](https://github.com/babybuddy/babybuddy/issues/46)

**Merged pull requests:**

- Modify app manifest to fix iOS link issue. Fixes \#57. [\#58](https://github.com/babybuddy/babybuddy/pull/58) ([HorizonXP](https://github.com/HorizonXP))

## [v1.1.0](https://github.com/babybuddy/babybuddy/tree/v1.1.0) (2018-05-20)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.0.3...v1.1.0)

**Fixed bugs:**

- DoesNotExist error on feeding add with fresh install [\#37](https://github.com/babybuddy/babybuddy/issues/37)

**Closed issues:**

- how to setup locale [\#48](https://github.com/babybuddy/babybuddy/issues/48)
- ARM \(i.e. Raspberry Pi\) install problematic [\#43](https://github.com/babybuddy/babybuddy/issues/43)
- modul Image missing [\#42](https://github.com/babybuddy/babybuddy/issues/42)
- sha256 of docopt does not match [\#41](https://github.com/babybuddy/babybuddy/issues/41)
- New logo for Babybuddy [\#38](https://github.com/babybuddy/babybuddy/issues/38)
- Improve dashboard mobile performance [\#31](https://github.com/babybuddy/babybuddy/issues/31)

**Merged pull requests:**

- tackle the manual a bit. [\#45](https://github.com/babybuddy/babybuddy/pull/45) ([novski](https://github.com/novski))
- correct text to previous PR [\#44](https://github.com/babybuddy/babybuddy/pull/44) ([novski](https://github.com/novski))
- manual build corrections in readme.md [\#40](https://github.com/babybuddy/babybuddy/pull/40) ([novski](https://github.com/novski))
- New logo for Babybuddy [\#39](https://github.com/babybuddy/babybuddy/pull/39) ([reallinfo](https://github.com/reallinfo))

## [v1.0.3](https://github.com/babybuddy/babybuddy/tree/v1.0.3) (2018-03-28)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.0.2...v1.0.3)

**Closed issues:**

- Configurable units? [\#36](https://github.com/babybuddy/babybuddy/issues/36)

## [v1.0.2](https://github.com/babybuddy/babybuddy/tree/v1.0.2) (2018-03-04)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.0.1...v1.0.2)

**Closed issues:**

- Add photo field to Child model [\#13](https://github.com/babybuddy/babybuddy/issues/13)

**Merged pull requests:**

- Add support for AWS S3 storage for ephemeral storage platforms [\#33](https://github.com/babybuddy/babybuddy/pull/33) ([overshard](https://github.com/overshard))

## [v1.0.1](https://github.com/babybuddy/babybuddy/tree/v1.0.1) (2018-01-25)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/v1.0.0...v1.0.1)

## [v1.0.0](https://github.com/babybuddy/babybuddy/tree/v1.0.0) (2017-12-30)

[Full Changelog](https://github.com/babybuddy/babybuddy/compare/9261e512bc74f813226c34273875a588c5a80596...v1.0.0)

**Closed issues:**

- Refresh dashboard without full reload [\#30](https://github.com/babybuddy/babybuddy/issues/30)
- Add API tests [\#29](https://github.com/babybuddy/babybuddy/issues/29)
- Documentation on the API [\#28](https://github.com/babybuddy/babybuddy/issues/28)
- Fix reset command test [\#27](https://github.com/babybuddy/babybuddy/issues/27)
- Add basic users management [\#26](https://github.com/babybuddy/babybuddy/issues/26)
- Add status messages [\#25](https://github.com/babybuddy/babybuddy/issues/25)
- Add an average feeding time graph [\#23](https://github.com/babybuddy/babybuddy/issues/23)
- Use .env file for environment/settings variables [\#22](https://github.com/babybuddy/babybuddy/issues/22)
- Docker installation [\#21](https://github.com/babybuddy/babybuddy/issues/21)
- Add fixtures and improve tests [\#18](https://github.com/babybuddy/babybuddy/issues/18)
- Add a welcome/intro page [\#17](https://github.com/babybuddy/babybuddy/issues/17)
- Improve Timeline view and placement. [\#16](https://github.com/babybuddy/babybuddy/issues/16)
- Add Weight tracking [\#15](https://github.com/babybuddy/babybuddy/issues/15)
- Improve dashboard view for \> 1 child [\#14](https://github.com/babybuddy/babybuddy/issues/14)
- Add filtering on all lists and API [\#12](https://github.com/babybuddy/babybuddy/issues/12)
- Handle custom data validation for forms [\#11](https://github.com/babybuddy/babybuddy/issues/11)
- Improve child delete confirmation flow [\#8](https://github.com/babybuddy/babybuddy/issues/8)
- Datetime pickers broken [\#6](https://github.com/babybuddy/babybuddy/issues/6)
- Use Visibilty API on dashboard [\#5](https://github.com/babybuddy/babybuddy/issues/5)
- Provide averages data [\#4](https://github.com/babybuddy/babybuddy/issues/4)
- Review/refactor handling of timezone information [\#3](https://github.com/babybuddy/babybuddy/issues/3)
- HTTP 500 on sleep pattern graph when no sleep entries exist [\#2](https://github.com/babybuddy/babybuddy/issues/2)
- Task 'migrate' is not in your gulpfile [\#1](https://github.com/babybuddy/babybuddy/issues/1)

**Merged pull requests:**

- Make ALLOW\_UPLOADS a setting dependent on user preference and platform [\#20](https://github.com/babybuddy/babybuddy/pull/20) ([overshard](https://github.com/overshard))
- Add ability to upload picture of child with thumbnailing capabilities. [\#19](https://github.com/babybuddy/babybuddy/pull/19) ([overshard](https://github.com/overshard))
- Add validation for model durations [\#10](https://github.com/babybuddy/babybuddy/pull/10) ([youngbob](https://github.com/youngbob))
- Fix style for datetime picker [\#9](https://github.com/babybuddy/babybuddy/pull/9) ([youngbob](https://github.com/youngbob))



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
