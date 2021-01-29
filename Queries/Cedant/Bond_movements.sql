SELECT
    CASE
        WHEN COMP_ID_PREV IS NULL THEN COMP_ID_CURR
        ELSE COMP_ID_PREV
    END AS COMP_ID,
    CASE
        WHEN ECAP_PREV_QRT IS NULL THEN 0
        ELSE ECAP_PREV_QRT
    END AS ECAP_PREV_QRT,
    CASE
        WHEN ECAP_CURR_QRT IS NULL THEN 0
        ELSE ECAP_CURR_QRT
    END AS ECAP_CURR_QRT
FROM
    (
        SELECT
            *
        FROM
            (
                SELECT
                    SUBSTR(CONTRACT_ID, 0, 5) AS COMP_ID_PREV,
                    SUM(EC_CONSUMPTION_ND) AS ECAP_PREV_QRT
                FROM
                    CALCXXXX.SO_REPORTING -- should correspond to previous quarter
                WHERE
                    MODEL_TYPE = 'IR'
                    AND MODEL_SUB_TYPE LIKE 'BO_%'
                GROUP BY
                    SUBSTR(CONTRACT_ID, 0, 5)
            ) old FULL OUTER JOIN (
                SELECT
                    SUBSTR(CONTRACT_ID, 0, 5) AS COMP_ID_CURR,
                    SUM(EC_CONSUMPTION_ND) AS ECAP_CURR_QRT
                FROM
                    CALCXXXX.SO_REPORTING -- should correspond to current quarter
                WHERE
                    MODEL_TYPE = 'IR'
                    AND MODEL_SUB_TYPE LIKE 'BO_%'
                GROUP BY
                    SUBSTR(CONTRACT_ID, 0, 5)
            ) new ON old.COMP_ID_PREV = new.COMP_ID_CURR
    )
