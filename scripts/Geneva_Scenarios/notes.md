# Geneva Scenarios Notes

## Overview
Four scenarios were considered in the paper, comparing TOTEX optimization with and without electrification, plus actor-based constraints and sensitivity analysis.

## Scenarios

### 1. 9a_TOTEX_Geneva_wo_EL.py - TOTEX without Electrification
Minimizes total expenditure (TOTEX) without allowing electrification technologies.

**Key constraints:**
- Excludes: Heat pumps, PV, batteries, electrical heaters, thermal solar (`9a_TOTEX_Geneva_wo_EL.py:30`)
- Actor profits limited to interest rate × their investments (landlord, ECM, DSO)
- **NO subsidies allowed** (`9a_TOTEX_Geneva_wo_EL.py:26`)
- Tenant costs can be constrained by income (`9a_TOTEX_Geneva_wo_EL.py:64`)

**Configuration:**
- Comment out line 64 to remove tenant cost limits
- Modify epsilon constraints at `../model/ampl_model/actors_problem.mod:122, 161, 189` to adjust profit limits

---

### 2. 9b_TOTEX_Geneva.py - TOTEX with Electrification
Same as scenario 9a but allows electrification technologies (EVs, heat pumps, etc.).

**Key difference:** Electrification units are included in the optimization.

---

### 3. 9c_Actors_Geneva.py - Actor Boundaries
Explicitly considers actor-specific constraints and boundaries.

**Renter constraints:**
- Uses baseline TOTEX from `9a_{neighborhood_type}_TOTEX_wo_El.pickle` as reference cost
- Function `get_renter_param()` (`9c_Actors_Geneva.py:7-63`) computes reference costs from 9a results
- Renter affordability parameter allows scaling from baseline costs

**Configuration:**
- Uncomment `../model/ampl_model/actors_problem.mod:75` to enable renter affordability constraints
- Set `renter_affordability` parameter (default = 1.0 means 100% of baseline cost)

---

### 4. 9d_Actors_Geneva_sens.py - Sensitivity Analysis
Performs sensitivity analysis on tenant affordability and interest rates.

**Method:**
- Uses Sobol sampling to generate parameter combinations
- Tests various affordability levels and interest rate scenarios
