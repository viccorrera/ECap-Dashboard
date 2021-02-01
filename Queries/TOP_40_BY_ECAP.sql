SELECT
    ULTIMATE_ID_NEW,
    ULTIMATE_NAME_NEW,
    NO_CUSTOMERS_OLD,
    NO_CUSTOMERS_NEW,
    PD_OLD,
    PD_NEW,
    CASE
        WHEN PD_OLD IS NULL THEN PD_NEW
        ELSE PD_NEW - PD_OLD
    END AS PD_DELTA,
    EXPOSURE_OLD,
    EXPOSURE_NEW,
    CASE
        WHEN EXPOSURE_OLD IS NULL THEN EXPOSURE_NEW
        ELSE EXPOSURE_NEW - EXPOSURE_OLD
    END AS EXP_DELTA,
    ECAP_OLD,
    ECAP_NEW,
    CASE
        WHEN ECAP_OLD IS NULL THEN ECAP_NEW
        ELSE ECAP_NEW - ECAP_OLD
    END AS ECAP_DELTA,
    ULTIMATE_RATING_TYPE_OLD,
    ULTIMATE_RATING_OLD,
    ULTIMATE_RATING_TYPE_NEW,
    ULTIMATE_RATING_NEW,
    ECAP_OLD / EXPOSURE_OLD as Ecap_TPE_OLD,
    ECAP_NEW / EXPOSURE_NEW as Ecap_TPE_NEW
FROM
    (
        (
            WITH INRE_COM_DATA_NEW AS (
                -- Extract of commercial exposure and ECAP aggregated at parent level
                SELECT
                    DISTINCT ULTIMATE_ID,
                    ULTIMATE_NAME,
                    ULTIMATE_RATING,
                    ULTIMATE_RATING_TYPE,
                    COUNT(DISTINCT(CUSTOMER_ID)) AS No_Customers,
                    SUM(EC_CONSUMPTION_ND) AS ECAP,
                    SUM(CREDIT_LIMIT_NET_EXPOSURE) AS EXPOSURE,
                    SUM(CREDIT_LIMIT_NET_EXPOSURE * ULTIMATE_POD) / SUM(CREDIT_LIMIT_NET_EXPOSURE) AS PD
                FROM
                    CALCXXXX.SO_REPORTING -- This should correspond to the new schema
                WHERE
                    model_type = 'IR'
                    AND MODEL_SUB_TYPE IN ('CI_COM_KN', 'BO_COM_KN')
                GROUP BY
                    ULTIMATE_ID,
                    ULTIMATE_NAME,
                    ULTIMATE_RATING,
                    ULTIMATE_RATING_TYPE
            )
            SELECT
                a.ULTIMATE_ID AS ULTIMATE_ID_NEW,
                a.ULTIMATE_NAME AS ULTIMATE_NAME_NEW,
                a.ULTIMATE_RATING_TYPE AS ULTIMATE_RATING_TYPE_NEW,
                a.ULTIMATE_RATING AS ULTIMATE_RATING_NEW,
                a.PD AS PD_NEW,
                a.NO_CUSTOMERS AS No_CUSTOMERS_NEW,
                a.EXPOSURE AS EXPOSURE_NEW,
                a.ECAP AS COM_ECAP_NEW,
                POL_ECAP AS POL_ECAP_NEW,
                CASE
                    WHEN POL_ECAP IS NULL THEN ECAP
                    ELSE ECAP + POL_ECAP
                END AS ECAP_NEW -- Adding political exposure extracted below to the above commercial exposure
            FROM
                INRE_COM_DATA_NEW a
                LEFT JOIN (
                    SELECT
                        DISTINCT b.ULTIMATE_ID AS POL_ULTIMATE_ID,
                        SUM(b.EC_CONSUMPTION_ND) AS POL_ECAP -- Extract of political exposure aggregated at parent level
                    FROM
                        CALCXXXX.SO_REPORTING -- This should correspond to the new schema
                    WHERE
                        b.MODEL_TYPE = 'IR'
                        AND b.MODEL_SUB_TYPE = 'CI_POL_KN'
                    GROUP BY
                        b.ULTIMATE_ID
                ) ON a.ULTIMATE_ID = POL_ULTIMATE_ID
            ORDER BY
                ECAP_NEW DESC -- Ordering resulting ECAP by descending order which will allow us to use the function ROWNUM to extract the top 40 rows (see last line of query)
        )
        LEFT JOIN (
            -- Joining in data from previous position
            WITH INRE_COM_DATA_OLD AS (
                SELECT
                    DISTINCT -- this query aggregates ECAP and Exposure at parent level, ordered by decreasing ECAP consumption
                    ULTIMATE_ID,
                    ULTIMATE_NAME,
                    ULTIMATE_RATING,
                    ULTIMATE_RATING_TYPE,
                    COUNT(DISTINCT(CUSTOMER_ID)) AS No_Customers,
                    SUM(EC_CONSUMPTION_ND) AS ECAP,
                    SUM(CREDIT_LIMIT_NET_EXPOSURE) AS EXPOSURE,
                    SUM(CREDIT_LIMIT_NET_EXPOSURE * ULTIMATE_POD) / SUM(CREDIT_LIMIT_NET_EXPOSURE) AS PD
                FROM
                    CALCXXXX.SO_REPORTING -- This should correspond to the old schema
                WHERE
                    model_type = 'IR'
                    AND MODEL_SUB_TYPE IN ('CI_COM_KN', 'BO_COM_KN')
                GROUP BY
                    ULTIMATE_ID,
                    ULTIMATE_NAME,
                    ULTIMATE_RATING,
                    ULTIMATE_RATING_TYPE
            )
            SELECT
                c.ULTIMATE_ID AS ULTIMATE_ID_OLD,
                c.ULTIMATE_NAME AS ULTIMATE_NAME_OLD,
                c.ULTIMATE_RATING_TYPE AS ULTIMATE_RATING_TYPE_OLD,
                c.ULTIMATE_RATING AS ULTIMATE_RATING_OLD,
                c.PD AS PD_OLD,
                c.NO_CUSTOMERS AS No_CUSTOMERS_OLD,
                c.EXPOSURE AS EXPOSURE_OLD,
                c.ECAP AS COM_ECAP_OLD,
                POL_ECAP AS POL_ECAP_OLD,
                CASE
                    WHEN POL_ECAP IS NULL THEN ECAP
                    ELSE ECAP + POL_ECAP
                END AS ECAP_OLD
            FROM
                INRE_COM_DATA_OLD c
                LEFT JOIN (
                    SELECT
                        DISTINCT d.ULTIMATE_ID AS POL_ULTIMATE_ID,
                        SUM(d.EC_CONSUMPTION_ND) AS POL_ECAP
                    FROM
                        CALCXXXX.SO_REPORTING -- This should correspond to the old schema
                    WHERE
                        d.MODEL_TYPE = 'IR'
                        AND d.MODEL_SUB_TYPE = 'CI_POL_KN'
                    GROUP BY
                        d.ULTIMATE_ID
                ) ON c.ULTIMATE_ID = POL_ULTIMATE_ID
        ) ON ULTIMATE_ID_NEW = ULTIMATE_ID_OLD
    )
WHERE
    ROWNUM <= 40;
