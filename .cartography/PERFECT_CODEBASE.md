# 🏛️ PERFECT CODEBASE (LLM SOURCE)


### FILE: macros\cents_to_dollars.sql
```
{# A basic example for a project-wide macro to cast a column uniformly #}

{% macro cents_to_dollars(column_name) -%}
    {{ return(adapter.dispatch('cents_to_dollars')(column_name)) }}
{%- endmacro %}

{% macro default__cents_to_dollars(column_name) -%}
    ({{ column_name }} / 100)::numeric(16, 2)
{%- endmacro %}

{% macro postgres__cents_to_dollars(column_name) -%}
    ({{ column_name }}::numeric(16, 2) / 100)
{%- endmacro %}

{% macro bigquery__cents_to_dollars(column_name) %}
    round(cast(({{ column_name }} / 100) as numeric), 2)
{% endmacro %}

{% macro fabric__cents_to_dollars(column_name) %}
    cast({{ column_name }} / 100 as numeric(16,2))
{% endmacro %}

```

### FILE: macros\generate_schema_name.sql
```
{% macro generate_schema_name(custom_schema_name, node) %}

    {% set default_schema = target.schema %}

    {# seeds go in a global `raw` schema #}
    {% if node.resource_type == 'seed' %}
        {{ custom_schema_name | trim }}

    {# non-specified schemas go to the default target schema #}
    {% elif custom_schema_name is none %}
        {{ default_schema }}


    {# specified custom schema names go to the schema name prepended with the the default schema name in prod (as this is an example project we want the schemas clearly labeled) #}
    {% elif target.name == 'prod' %}
        {{ default_schema }}_{{ custom_schema_name | trim }}

    {# specified custom schemas go to the default target schema for non-prod targets #}
    {% else %}
        {{ default_schema }}
    {% endif %}

{% endmacro %}

```

### FILE: models\marts\customers.sql
```
with

customers as (

    select * from {{ ref('stg_customers') }}

),

orders as (

    select * from {{ ref('orders') }}

),

customer_orders_summary as (

    select
        orders.customer_id,

        count(distinct orders.order_id) as count_lifetime_orders,
        count(distinct orders.order_id) > 1 as is_repeat_buyer,
        min(orders.ordered_at) as first_ordered_at,
        max(orders.ordered_at) as last_ordered_at,
        sum(orders.subtotal) as lifetime_spend_pretax,
        sum(orders.tax_paid) as lifetime_tax_paid,
        sum(orders.order_total) as lifetime_spend

    from orders

    group by 1

),

joined as (

    select
        customers.*,

        customer_orders_summary.count_lifetime_orders,
        customer_orders_summary.first_ordered_at,
        customer_orders_summary.last_ordered_at,
        customer_orders_summary.lifetime_spend_pretax,
        customer_orders_summary.lifetime_tax_paid,
        customer_orders_summary.lifetime_spend,

        case
            when customer_orders_summary.is_repeat_buyer then 'returning'
            else 'new'
        end as customer_type

    from customers

    left join customer_orders_summary
        on customers.customer_id = customer_orders_summary.customer_id

)

select * from joined

```

### FILE: models\marts\locations.sql
```
with

locations as (

    select * from {{ ref('stg_locations') }}

)

select * from locations

```

### FILE: models\marts\metricflow_time_spine.sql
```
-- metricflow_time_spine.sql
with

days as (

    --for BQ adapters use "DATE('01/01/2000','mm/dd/yyyy')"
    {{ dbt_date.get_base_dates(n_dateparts=365*10, datepart="day") }}

),

cast_to_date as (

    select cast(date_day as date) as date_day

    from days

)

select * from cast_to_date

```

### FILE: models\marts\orders.sql
```
with

orders as (

    select * from {{ ref('stg_orders') }}

),

order_items as (

    select * from {{ ref('order_items') }}

),

order_items_summary as (

    select
        order_id,

        sum(supply_cost) as order_cost,
        sum(product_price) as order_items_subtotal,
        count(order_item_id) as count_order_items,
        sum(
            case
                when is_food_item then 1
                else 0
            end
        ) as count_food_items,
        sum(
            case
                when is_drink_item then 1
                else 0
            end
        ) as count_drink_items

    from order_items

    group by 1

),

compute_booleans as (

    select
        orders.*,

        order_items_summary.order_cost,
        order_items_summary.order_items_subtotal,
        order_items_summary.count_food_items,
        order_items_summary.count_drink_items,
        order_items_summary.count_order_items,
        order_items_summary.count_food_items > 0 as is_food_order,
        order_items_summary.count_drink_items > 0 as is_drink_order

    from orders

    left join
        order_items_summary
        on orders.order_id = order_items_summary.order_id

),

customer_order_count as (

    select
        *,

        row_number() over (
            partition by customer_id
            order by ordered_at asc
        ) as customer_order_number

    from compute_booleans

)

select * from customer_order_count

```

### FILE: models\marts\order_items.sql
```
with

order_items as (

    select * from {{ ref('stg_order_items') }}

),


orders as (

    select * from {{ ref('stg_orders') }}

),

products as (

    select * from {{ ref('stg_products') }}

),

supplies as (

    select * from {{ ref('stg_supplies') }}

),

order_supplies_summary as (

    select
        product_id,

        sum(supply_cost) as supply_cost

    from supplies

    group by 1

),

joined as (

    select
        order_items.*,

        orders.ordered_at,

        products.product_name,
        products.product_price,
        products.is_food_item,
        products.is_drink_item,

        order_supplies_summary.supply_cost

    from order_items

    left join orders on order_items.order_id = orders.order_id

    left join products on order_items.product_id = products.product_id

    left join order_supplies_summary
        on order_items.product_id = order_supplies_summary.product_id

)

select * from joined

```

### FILE: models\marts\products.sql
```
with

products as (

    select * from {{ ref('stg_products') }}

)

select * from products

```

### FILE: models\marts\supplies.sql
```
with

supplies as (

    select * from {{ ref('stg_supplies') }}

)

select * from supplies

```

### FILE: models\staging\stg_customers.sql
```
with

source as (

    select * from {{ source('ecom', 'raw_customers') }}

),

renamed as (

    select

        ----------  ids
        id as customer_id,

        ---------- text
        name as customer_name

    from source

)

select * from renamed

```

### FILE: models\staging\stg_locations.sql
```
with

source as (

    select * from {{ source('ecom', 'raw_stores') }}

),

renamed as (

    select

        ----------  ids
        id as location_id,

        ---------- text
        name as location_name,

        ---------- numerics
        tax_rate,

        ---------- timestamps
        {{ dbt.date_trunc('day', 'opened_at') }} as opened_date

    from source

)

select * from renamed

```

### FILE: models\staging\stg_orders.sql
```
with

source as (

    select * from {{ source('ecom', 'raw_orders') }}

),

renamed as (

    select

        ----------  ids
        id as order_id,
        store_id as location_id,
        customer as customer_id,

        ---------- numerics
        subtotal as subtotal_cents,
        tax_paid as tax_paid_cents,
        order_total as order_total_cents,
        {{ cents_to_dollars('subtotal') }} as subtotal,
        {{ cents_to_dollars('tax_paid') }} as tax_paid,
        {{ cents_to_dollars('order_total') }} as order_total,

        ---------- timestamps
        {{ dbt.date_trunc('day','ordered_at') }} as ordered_at

    from source

)

select * from renamed

```

### FILE: models\staging\stg_order_items.sql
```
with

source as (

    select * from {{ source('ecom', 'raw_items') }}

),

renamed as (

    select

        ----------  ids
        id as order_item_id,
        order_id,
        sku as product_id

    from source

)

select * from renamed

```

### FILE: models\staging\stg_products.sql
```
with

source as (

    select * from {{ source('ecom', 'raw_products') }}

),

renamed as (

    select

        ----------  ids
        sku as product_id,

        ---------- text
        name as product_name,
        type as product_type,
        description as product_description,


        ---------- numerics
        {{ cents_to_dollars('price') }} as product_price,

        ---------- booleans
        coalesce(type = 'jaffle', false) as is_food_item,

        coalesce(type = 'beverage', false) as is_drink_item

    from source

)

select * from renamed

```

### FILE: models\staging\stg_supplies.sql
```
with

source as (

    select * from {{ source('ecom', 'raw_supplies') }}

),

renamed as (

    select

        ----------  ids
        {{ dbt_utils.generate_surrogate_key(['id', 'sku']) }} as supply_uuid,
        id as supply_id,
        sku as product_id,

        ---------- text
        name as supply_name,

        ---------- numerics
        {{ cents_to_dollars('cost') }} as supply_cost,

        ---------- booleans
        perishable as is_perishable_supply

    from source

)

select * from renamed

```

### FILE: .github\workflows\scripts\dbt_cloud_run_job.py
```
import os
import time
import requests

# ------------------------------------------------------------------------------
# get environment variables
# ------------------------------------------------------------------------------
api_base = os.getenv(
    "DBT_URL", "https://cloud.getdbt.com"
)  # default to multitenant url
job_cause = os.getenv(
    "DBT_JOB_CAUSE", "API-triggered job"
)  # default to generic message
git_branch = os.getenv("DBT_JOB_BRANCH", None)  # default to None
schema_override = os.getenv("DBT_JOB_SCHEMA_OVERRIDE", None)  # default to None
api_key = os.environ[
    "DBT_API_KEY"
]  # no default here, just throw an error here if key not provided
account_id = os.environ[
    "DBT_ACCOUNT_ID"
]  # no default here, just throw an error here if id not provided
project_id = os.environ[
    "DBT_PROJECT_ID"
]  # no default here, just throw an error here if id not provided
job_id = os.environ[
    "DBT_PR_JOB_ID"
]  # no default here, just throw an error here if id not provided

print(f"""
Configuration:
api_base: {api_base}
job_cause: {job_cause}
git_branch: {git_branch}
schema_override: {schema_override}
account_id: {account_id}
project_id: {project_id}
job_id: {job_id}
""")

req_auth_header = {"Authorization": f"Token {api_key}"}
req_job_url = f"{api_base}/api/v2/accounts/{account_id}/jobs/{job_id}/run/"
run_status_map = {  # dbt run statuses are encoded as integers. This map provides a human-readable status
    1: "Queued",
    2: "Starting",
    3: "Running",
    10: "Success",
    20: "Error",
    30: "Cancelled",
}

type AuthHeader = dict[str, str]


def run_job(
    url: str,
    headers: AuthHeader,
    cause: str,
    branch: str | None = None,
    schema_override: str | None = None,
) -> int:
    """
    Runs a dbt job
    """

    # build payload
    req_payload = {"cause": cause}
    if branch and not branch.startswith(
        "$("
    ):  # starts with '$(' indicates a valid branch name was not provided
        req_payload["git_branch"] = branch.replace("refs/heads/", "")
    if schema_override:
        req_payload["schema_override"] = schema_override.replace("-", "_").replace(
            "/", "_"
        )

    # trigger job
    print(f"Triggering job:\n\turl: {url}\n\tpayload: {req_payload}")

    response = requests.post(url, headers=headers, json=req_payload)
    run_id: int = response.json()["data"]["id"]
    return run_id


def get_run_status(url: str, headers: AuthHeader) -> str:
    """
    gets the status of a running dbt job
    """
    # get status
    response = requests.get(url, headers=headers)
    run_status_code: int = response.json()["data"]["status"]
    run_status = run_status_map[run_status_code]
    return run_status


def main():
    print("Beginning request for job run...")

    # run job
    run_id: int = 0
    try:
        run_id = run_job(
            req_job_url, req_auth_header, job_cause, git_branch, schema_override
        )
    except Exception as e:
        print(f"ERROR! - Could not trigger job:\n {e}")
        raise

    # build status check url and run status link
    req_status_url = f"{api_base}/api/v2/accounts/{account_id}/runs/{run_id}/"
    run_status_link = (
        f"{api_base}/deploy/{account_id}/projects/{project_id}/runs/{run_id}/"
    )

    # update user with status link
    print(f"Job running! See job status at {run_status_link}")

    # check status indefinitely with an initial wait period
    time.sleep(30)
    while True:
        status = get_run_status(req_status_url, req_auth_header)
        print(f"Run status -> {status}")

        if status in ["Error", "Cancelled"]:
            raise Exception(f"Run failed or canceled. See why at {run_status_link}")

        if status == "Success":
            print(f"Job completed successfully! See details at {run_status_link}")
            return

        time.sleep(10)


if __name__ == "__main__":
    main()

```
