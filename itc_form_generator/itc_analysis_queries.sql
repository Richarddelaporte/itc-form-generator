-- ===============================================
-- EXTRACT COMMON SECTIONS & QUESTIONS FROM FORMS
-- Purpose: Build equipment-specific templates
-- ===============================================

-- -----------------------------------------------
-- QUERY 1: TOP SECTIONS ACROSS ALL FORMS
-- Find the most common section names
-- -----------------------------------------------
SELECT
    layout_section_label as section_name,
    COUNT(*) as usage_count,
    COUNT(DISTINCT form_id) as num_forms
FROM idc_acc_form_responses_datamart
WHERE layout_section_label IS NOT NULL
    AND layout_section_label != ''
GROUP BY layout_section_label
ORDER BY usage_count DESC
LIMIT 100;


-- -----------------------------------------------
-- QUERY 2: TOP CHECK ITEMS ACROSS ALL FORMS
-- Find the most common check item questions
-- -----------------------------------------------
SELECT
    layout_section_item_label as check_item,
    COUNT(*) as usage_count,
    COUNT(DISTINCT form_id) as num_forms
FROM idc_acc_form_responses_datamart
WHERE layout_section_item_label IS NOT NULL
    AND layout_section_item_label != ''
GROUP BY layout_section_item_label
ORDER BY usage_count DESC
LIMIT 200;


-- -----------------------------------------------
-- QUERY 3: SECTIONS WITH THEIR CHECK ITEMS
-- See which items belong to which sections
-- -----------------------------------------------
SELECT
    layout_section_label as section_name,
    layout_section_item_label as check_item,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE layout_section_label IS NOT NULL
    AND layout_section_item_label IS NOT NULL
GROUP BY layout_section_label, layout_section_item_label
ORDER BY section_name, frequency DESC;


-- -----------------------------------------------
-- QUERY 4: RSB/RDB FORMS - Sections & Items
-- Row Switch Board / Row Distribution Board
-- -----------------------------------------------
SELECT
    layout_section_display_index as section_order,
    layout_section_label as section_name,
    layout_section_item_display_index as item_order,
    layout_section_item_label as check_item,
    presets,
    response_type,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(form_id) LIKE '%260401%'
   OR LOWER(layout_section_label) LIKE '%rsb%'
   OR LOWER(layout_section_label) LIKE '%rdb%'
   OR LOWER(layout_section_label) LIKE '%row%switch%'
   OR LOWER(layout_section_label) LIKE '%row%distribution%'
GROUP BY layout_section_display_index, layout_section_label,
         layout_section_item_display_index, layout_section_item_label,
         presets, response_type
ORDER BY section_order, item_order
LIMIT 500;


-- -----------------------------------------------
-- QUERY 5: ATS FORMS - Sections & Items
-- Automatic Transfer Switch
-- -----------------------------------------------
SELECT
    layout_section_display_index as section_order,
    layout_section_label as section_name,
    layout_section_item_display_index as item_order,
    layout_section_item_label as check_item,
    presets,
    response_type,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(form_id) LIKE '%260627%'
   OR LOWER(layout_section_label) LIKE '%ats%'
   OR LOWER(layout_section_label) LIKE '%transfer%switch%'
GROUP BY layout_section_display_index, layout_section_label,
         layout_section_item_display_index, layout_section_item_label,
         presets, response_type
ORDER BY section_order, item_order
LIMIT 500;


-- -----------------------------------------------
-- QUERY 6: GENERATOR FORMS - Sections & Items
-- Diesel Generator
-- -----------------------------------------------
SELECT
    layout_section_display_index as section_order,
    layout_section_label as section_name,
    layout_section_item_display_index as item_order,
    layout_section_item_label as check_item,
    presets,
    response_type,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(form_id) LIKE '%260620%'
   OR LOWER(layout_section_label) LIKE '%generator%'
   OR LOWER(layout_section_label) LIKE '%genset%'
GROUP BY layout_section_display_index, layout_section_label,
         layout_section_item_display_index, layout_section_item_label,
         presets, response_type
ORDER BY section_order, item_order
LIMIT 500;


-- -----------------------------------------------
-- QUERY 7: UPS FORMS - Sections & Items
-- Uninterruptible Power Supply
-- -----------------------------------------------
SELECT
    layout_section_display_index as section_order,
    layout_section_label as section_name,
    layout_section_item_display_index as item_order,
    layout_section_item_label as check_item,
    presets,
    response_type,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(form_id) LIKE '%260614%'
   OR LOWER(layout_section_label) LIKE '%ups%'
   OR LOWER(layout_section_label) LIKE '%uninterruptible%'
GROUP BY layout_section_display_index, layout_section_label,
         layout_section_item_display_index, layout_section_item_label,
         presets, response_type
ORDER BY section_order, item_order
LIMIT 500;


-- -----------------------------------------------
-- QUERY 8: TRANSFORMER FORMS - Sections & Items
-- -----------------------------------------------
SELECT
    layout_section_display_index as section_order,
    layout_section_label as section_name,
    layout_section_item_display_index as item_order,
    layout_section_item_label as check_item,
    presets,
    response_type,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(form_id) LIKE '%260320%'
   OR LOWER(layout_section_label) LIKE '%transformer%'
   OR LOWER(layout_section_label) LIKE '%ptx%'
GROUP BY layout_section_display_index, layout_section_label,
         layout_section_item_display_index, layout_section_item_label,
         presets, response_type
ORDER BY section_order, item_order
LIMIT 500;


-- -----------------------------------------------
-- QUERY 9: FCU FORMS - Sections & Items
-- Fan Coil Unit
-- -----------------------------------------------
SELECT
    layout_section_display_index as section_order,
    layout_section_label as section_name,
    layout_section_item_display_index as item_order,
    layout_section_item_label as check_item,
    presets,
    response_type,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(form_id) LIKE '%238123%'
   OR LOWER(layout_section_label) LIKE '%fcu%'
   OR LOWER(layout_section_label) LIKE '%fan coil%'
GROUP BY layout_section_display_index, layout_section_label,
         layout_section_item_display_index, layout_section_item_label,
         presets, response_type
ORDER BY section_order, item_order
LIMIT 500;


-- -----------------------------------------------
-- QUERY 10: MV SWITCH FORMS - Sections & Items
-- Medium Voltage Switch
-- -----------------------------------------------
SELECT
    layout_section_display_index as section_order,
    layout_section_label as section_name,
    layout_section_item_display_index as item_order,
    layout_section_item_label as check_item,
    presets,
    response_type,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(form_id) LIKE '%260310%'
   OR LOWER(layout_section_label) LIKE '%mv%switch%'
   OR LOWER(layout_section_label) LIKE '%medium%voltage%'
GROUP BY layout_section_display_index, layout_section_label,
         layout_section_item_display_index, layout_section_item_label,
         presets, response_type
ORDER BY section_order, item_order
LIMIT 500;


-- -----------------------------------------------
-- QUERY 11: BATTERY FORMS - Sections & Items
-- VRLA Batteries
-- -----------------------------------------------
SELECT
    layout_section_display_index as section_order,
    layout_section_label as section_name,
    layout_section_item_display_index as item_order,
    layout_section_item_label as check_item,
    presets,
    response_type,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(form_id) LIKE '%260613%'
   OR LOWER(layout_section_label) LIKE '%battery%'
   OR LOWER(layout_section_label) LIKE '%vrla%'
GROUP BY layout_section_display_index, layout_section_label,
         layout_section_item_display_index, layout_section_item_label,
         presets, response_type
ORDER BY section_order, item_order
LIMIT 500;


-- -----------------------------------------------
-- QUERY 12: COMMON PRESETS/ACCEPTANCE CRITERIA
-- What are the standard response options?
-- -----------------------------------------------
SELECT
    presets,
    response_type,
    COUNT(*) as usage_count,
    COUNT(DISTINCT form_id) as num_forms
FROM idc_acc_form_responses_datamart
WHERE presets IS NOT NULL
    AND presets != ''
GROUP BY presets, response_type
ORDER BY usage_count DESC
LIMIT 100;


-- -----------------------------------------------
-- QUERY 13: SAMPLE COMPLETE FPT FORM
-- Get one complete FPT form to see full structure
-- -----------------------------------------------
WITH fpt_form AS (
    SELECT form_id
    FROM idc_acc_form_responses_datamart
    WHERE LOWER(form_id) LIKE '%functionalperformancetest%'
       OR LOWER(native_form_id) LIKE '%fpt%'
    GROUP BY form_id
    HAVING COUNT(*) > 10
    LIMIT 1
)
SELECT
    f.form_id,
    f.layout_section_display_index as section_order,
    f.layout_section_label as section_name,
    f.layout_section_item_display_index as item_order,
    f.layout_section_item_label as check_item,
    f.presets,
    f.response_type
FROM idc_acc_form_responses_datamart f
JOIN fpt_form ff ON f.form_id = ff.form_id
ORDER BY f.layout_section_display_index, f.layout_section_item_display_index;


-- -----------------------------------------------
-- QUERY 14: COMMON SAFETY/INTERLOCK ITEMS
-- Safety-related check items across all forms
-- -----------------------------------------------
SELECT
    layout_section_label as section_name,
    layout_section_item_label as check_item,
    presets,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(layout_section_item_label) LIKE '%safety%'
   OR LOWER(layout_section_item_label) LIKE '%interlock%'
   OR LOWER(layout_section_item_label) LIKE '%emergency%'
   OR LOWER(layout_section_item_label) LIKE '%shutdown%'
   OR LOWER(layout_section_item_label) LIKE '%e-stop%'
   OR LOWER(layout_section_item_label) LIKE '%fire%'
   OR LOWER(layout_section_item_label) LIKE '%smoke%'
GROUP BY layout_section_label, layout_section_item_label, presets
ORDER BY frequency DESC
LIMIT 100;


-- -----------------------------------------------
-- QUERY 15: COMMON ALARM ITEMS
-- Alarm-related check items
-- -----------------------------------------------
SELECT
    layout_section_label as section_name,
    layout_section_item_label as check_item,
    presets,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(layout_section_item_label) LIKE '%alarm%'
   OR LOWER(layout_section_item_label) LIKE '%alert%'
   OR LOWER(layout_section_item_label) LIKE '%fault%'
   OR LOWER(layout_section_item_label) LIKE '%warning%'
GROUP BY layout_section_label, layout_section_item_label, presets
ORDER BY frequency DESC
LIMIT 100;


-- -----------------------------------------------
-- QUERY 16: COMMON BMS/COMMUNICATION ITEMS
-- BMS and communication check items
-- -----------------------------------------------
SELECT
    layout_section_label as section_name,
    layout_section_item_label as check_item,
    presets,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(layout_section_item_label) LIKE '%bms%'
   OR LOWER(layout_section_item_label) LIKE '%scada%'
   OR LOWER(layout_section_item_label) LIKE '%modbus%'
   OR LOWER(layout_section_item_label) LIKE '%communication%'
   OR LOWER(layout_section_item_label) LIKE '%network%'
   OR LOWER(layout_section_item_label) LIKE '%point%'
GROUP BY layout_section_label, layout_section_item_label, presets
ORDER BY frequency DESC
LIMIT 100;


-- -----------------------------------------------
-- QUERY 17: COMMON MEASUREMENT ITEMS
-- Items requiring numeric measurements
-- -----------------------------------------------
SELECT
    layout_section_label as section_name,
    layout_section_item_label as check_item,
    presets,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE response_type = 'number'
   OR LOWER(layout_section_item_label) LIKE '%measure%'
   OR LOWER(layout_section_item_label) LIKE '%record%'
   OR LOWER(layout_section_item_label) LIKE '%voltage%'
   OR LOWER(layout_section_item_label) LIKE '%current%'
   OR LOWER(layout_section_item_label) LIKE '%temperature%'
   OR LOWER(layout_section_item_label) LIKE '%pressure%'
GROUP BY layout_section_label, layout_section_item_label, presets
ORDER BY frequency DESC
LIMIT 100;


-- -----------------------------------------------
-- QUERY 18: COMMON VERIFICATION ITEMS
-- Verification-type check items
-- -----------------------------------------------
SELECT
    layout_section_label as section_name,
    layout_section_item_label as check_item,
    presets,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(layout_section_item_label) LIKE '%verify%'
   OR LOWER(layout_section_item_label) LIKE '%confirm%'
   OR LOWER(layout_section_item_label) LIKE '%check%'
   OR LOWER(layout_section_item_label) LIKE '%inspect%'
GROUP BY layout_section_label, layout_section_item_label, presets
ORDER BY frequency DESC
LIMIT 100;


-- -----------------------------------------------
-- QUERY 19: MUA/MAKEUP AIR FORMS - Sections & Items
-- (If any exist in the data)
-- -----------------------------------------------
SELECT
    layout_section_display_index as section_order,
    layout_section_label as section_name,
    layout_section_item_display_index as item_order,
    layout_section_item_label as check_item,
    presets,
    response_type,
    COUNT(*) as frequency
FROM idc_acc_form_responses_datamart
WHERE LOWER(form_id) LIKE '%mua%'
   OR LOWER(form_id) LIKE '%makeup%'
   OR LOWER(layout_section_label) LIKE '%mua%'
   OR LOWER(layout_section_label) LIKE '%makeup%'
   OR LOWER(layout_section_label) LIKE '%make up%'
   OR LOWER(layout_section_item_label) LIKE '%mua%'
   OR LOWER(layout_section_item_label) LIKE '%makeup%air%'
GROUP BY layout_section_display_index, layout_section_label,
         layout_section_item_display_index, layout_section_item_label,
         presets, response_type
ORDER BY section_order, item_order
LIMIT 500;


-- -----------------------------------------------
-- QUERY 20: SECTION STRUCTURE BY FORM TYPE
-- How sections are organized in different form types
-- -----------------------------------------------
SELECT
    CASE
        WHEN form_id LIKE '%CEV%' THEN 'CEV'
        WHEN form_id LIKE '%FunctionalPerformanceTest%' THEN 'FPT'
        WHEN form_id LIKE '%SetInPlace%' THEN 'SetInPlace'
        WHEN form_id LIKE '%PreEnergization%' THEN 'PreEnergization'
        WHEN form_id LIKE '%ManufacturerEquipmentPreStartup%' THEN 'ManufacturerPreStartup'
        ELSE 'Other'
    END as form_type,
    layout_section_label as section_name,
    COUNT(DISTINCT form_id) as num_forms,
    COUNT(*) as total_items
FROM idc_acc_form_responses_datamart
WHERE layout_section_label IS NOT NULL
GROUP BY 1, layout_section_label
ORDER BY form_type, total_items DESC;
