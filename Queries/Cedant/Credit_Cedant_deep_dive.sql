SELECT
    NVL(OLD_ALIAS_ID, NEW_ALIAS_ID) AS ALIAS_ID,
    NVL(OLD_PARENT_NAME, NEW_PARENT_NAME) AS PARENT_NAME,
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
    NEW_RATING,
    OLD_RSQUARED,
    NEW_RSQUARED,
    NVL(NEW_RSQUARED, 0) - NVL(OLD_RSQUARED, 0) AS DELTA_RSQUARED
FROM
    (
        SELECT
            *
        FROM
            (
                SELECT
                    ALIAS_ID AS OLD_ALIAS_ID,
                    SUBSTR(ULTIMATE_NAME, 0, 70) as OLD_PARENT_NAME,
                    SUM(
                        CASE
                            WHEN MODEL_SUB_TYPE LIKE 'CI_COM_%' THEN ULTIMATE_POD
                        END
                    ) AS OLD_PD,
                    SUM(
                        CASE
                            WHEN MODEL_SUB_TYPE LIKE 'CI_COM_%' THEN CREDIT_LIMIT_NET_EXPOSURE
                        END
                    ) AS OLD_EXP,
                    SUM(EC_CONSUMPTION_ND) AS OLD_ECAP,
                    MAX(ULTIMATE_RATING_TYPE) AS OLD_RATING_TYPE,
                    MAX(ULTIMATE_RATING) AS OLD_RATING,
                    SUM(
                        CASE
                            WHEN MODEL_SUB_TYPE LIKE 'CI_COM_%' THEN ULTIMATE_RSQUARED
                        END
                    ) AS OLD_RSQUARED
                FROM
                    CALCXXXX.SO_REPORTING -- UPDATE OLD QUARTER --
                WHERE
                    MODEL_TYPE LIKE 'IR'
                    AND MODEL_SUB_TYPE LIKE 'CI_%'
                    AND CUSTOMER_ID = '' -- UPDATE Customer ID
                GROUP BY
                    ALIAS_ID,
                    SUBSTR(ULTIMATE_NAME, 0, 70)
            ) x FULL OUTER JOIN (
                SELECT
                    ALIAS_ID AS NEW_ALIAS_ID,
                    SUBSTR(ULTIMATE_NAME, 0, 70) as NEW_PARENT_NAME,
                    SUM(
                        CASE
                            WHEN MODEL_SUB_TYPE LIKE 'CI_COM_%' THEN ULTIMATE_POD
                        END
                    ) AS NEW_PD,
                    SUM(
                        CASE
                            WHEN MODEL_SUB_TYPE LIKE 'CI_COM_%' THEN CREDIT_LIMIT_NET_EXPOSURE
                        END
                    ) AS NEW_EXP,
                    SUM(EC_CONSUMPTION_ND) AS NEW_ECAP,
                    MAX(ULTIMATE_RATING_TYPE) AS NEW_RATING_TYPE,
                    MAX(ULTIMATE_RATING) AS NEW_RATING,
                    SUM(
                        CASE
                            WHEN MODEL_SUB_TYPE LIKE 'CI_COM_%' THEN ULTIMATE_RSQUARED
                        END
                    ) AS NEW_RSQUARED
                FROM
                    CALCXXXX.SO_REPORTING -- UPDATE NEW QUARTER --
                WHERE
                    MODEL_TYPE LIKE 'IR'
                    AND MODEL_SUB_TYPE LIKE 'CI_%'
                    AND CUSTOMER_ID = '' -- UPDATE Customer ID
                GROUP BY
                    ALIAS_ID,
                    SUBSTR(ULTIMATE_NAME, 0, 70)
            ) y on x.OLD_ALIAS_ID = y.NEW_ALIAS_ID
    )
