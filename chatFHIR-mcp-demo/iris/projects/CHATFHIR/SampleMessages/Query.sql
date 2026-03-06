/* 
Selects all female patients with Pre-Diabetes diagnosis and a heart-rate above 90
*/

SELECT 
distinct pat.givenname, pat.familyname, pat.gender
FROM ChatFHIR.Observation obs, ChatFHIR.Patient pat, ChatFHIR.Condition con
Where obs.categorycode = 'vital-signs'
and obs.code = '8867-4' --- snomed code for heart-rate
and obs.valuequantity > 90
and obs.Patient = pat.key
and con.patient = pat.key
and con.snomedcode = 44054006 --- snomed code for Diabetes
and pat.gender = 'female'
