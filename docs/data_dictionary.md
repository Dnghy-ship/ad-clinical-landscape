# Data Dictionary

## studies.csv
一行一个 NCT study。

核心列：

- `nct_id`
- `phase`
- `overall_status`
- `lead_sponsor`
- `lead_sponsor_class`
- `intervention_names`
- `intervention_types`
- `mechanism_categories`
- `enrollment_count`
- `minimum_age`, `maximum_age`, `sex`
- `eligibility_criteria`
- `inclusion_summary`, `exclusion_summary`
- `primary_outcome_measures`
- `countries`, `site_count`
- `primary_completion_date`, `primary_completion_date_type`
- `completion_date`, `completion_date_type`
- `last_update_post_date`
- `ctgov_url`

## interventions.csv
一行一个 intervention。

重点看：

- `mechanism_category`
- `mechanism_confidence`
- `mechanism_source`

其中机制分类不是 ClinicalTrials.gov 的统一标准药理标签，而是本项目 annotation。

## primary_outcomes.csv
一行一个 primary outcome：

- `measure`
- `description`
- `time_frame`

## locations.csv
一行一个 trial site：

- `facility`
- `location_status`
- `city`
- `state`
- `country`
- `latitude`
- `longitude`

## changes.csv
第二次运行后记录：

- 新 study
- status 变化
- phase 变化
- completion timeline 变化
- last-update 变化
