SELECT
    NVL(ALIAS_ID_OLD, ALIAS_ID_NEW) AS ALIAS_ID,
    NVL(PARENT_NAME_OLD, PARENT_NAME_NEW) AS PARENT_NAME,
    NVL(OLD_PD, 0) AS OLD_PD,
    NVL(NEW_PD, 0) AS NEW_PD,
    NVL(NEW_PD, 0) - NVL(OLD_PD, 0) AS DELTA_PD,
    NVL(OLD_EXP, 0) AS OLD_EXP,
    NVL(NEW_EXP, 0) AS NEW_EXP,
    NVL(NEW_EXP, 0) - NVL(OLD_EXP, 0) AS DELTA_EXP,
    NVL(OLD_ECAP, 0) AS OLD_ECAP,
    NVL(NEW_ECAP, 0) AS NEW_ECAP,
    NVL(NEW_ECAP, 0) - NVL(OLD_ECAP, 0) AS DELTA_ECAP,
    OLD_RATING_TYPE,
    OLD_RATING,
    NEW_RATING_TYPE,
    NEW_RATING
FROM
    (
        SELECT
            *
        FROM
            (
                SELECT
                    ALIAS_ID AS ALIAS_ID_OLD,
                    TRIM('+' FROM (TRIM('"' FROM (SUBSTR(ULTIMATE_NAME, 0, 70))))) as PARENT_NAME_OLD,
                    SUM(CREDIT_LIMIT_NET_EXPOSURE * ULTIMATE_POD) / SUM(CREDIT_LIMIT_NET_EXPOSURE) AS OLD_PD,
                    SUM(CREDIT_LIMIT_NET_EXPOSURE) AS OLD_EXP,
                    SUM(EC_CONSUMPTION_ND) AS OLD_ECAP,
                    ULTIMATE_RATING_TYPE AS OLD_RATING_TYPE,
                    ULTIMATE_RATING AS OLD_RATING
                FROM
                    CALCXXXX.SO_REPORTING -- OLD QUARTER --
                WHERE
                    MODEL_TYPE LIKE 'IR'
                    AND MODEL_SUB_TYPE LIKE 'BO_%'
                    AND CUSTOMER_ID = '' -- Customer ID
                GROUP BY
                    ALIAS_ID,
                    ULTIMATE_NAME,
                    ULTIMATE_RATING_TYPE,
                    ULTIMATE_RATING
            ) x FULL OUTER JOIN (
                SELECT
                    ALIAS_ID AS ALIAS_ID_NEW,
                    TRIM('+' FROM (TRIM('"' FROM (SUBSTR(ULTIMATE_NAME, 0, 70))))) as PARENT_NAME_NEW,
                    SUM(CREDIT_LIMIT_NET_EXPOSURE * ULTIMATE_POD) / SUM(CREDIT_LIMIT_NET_EXPOSURE) AS NEW_PD,
                    SUM(CREDIT_LIMIT_NET_EXPOSURE) AS NEW_EXP,
                    SUM(EC_CONSUMPTION_ND) AS NEW_ECAP,
                    ULTIMATE_RATING_TYPE AS NEW_RATING_TYPE,
                    ULTIMATE_RATING AS NEW_RATING
                FROM
                    CALCXXXX.SO_REPORTING -- NEW QUARTER --
                WHERE
                    MODEL_TYPE LIKE 'IR'
                    AND MODEL_SUB_TYPE LIKE 'BO_%'
                    AND CUSTOMER_ID = '' -- Customer ID
                GROUP BY
                    ALIAS_ID,
                    ULTIMATE_NAME,
                    ULTIMATE_RATING_TYPE,
                    ULTIMATE_RATING
                ORDER BY
                    ALIAS_ID
            ) y on x.ALIAS_ID_OLD = y.ALIAS_ID_NEW
    )
