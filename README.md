# saas-mrr-waterfall-engine
An end-to-end Python financial analytics pipeline built with Pandas &amp; NumPy. Features point-in-time multi-currency FX conversion (pd.merge_asof), asynchronous event sequence reconstruction, automated 5-category MRR Waterfall categorization, and Cohort Net Revenue Retention (NRR) matrix calculation.
---

## 📌 Business Overview & Objective
This project builds an automated Monthly Recurring Revenue (MRR) engine for enterprise SaaS financial reporting. It transforms raw, asynchronous subscription event logs recorded across multiple global currencies (USD, EUR, VND) into standardized financial metrics, MRR Movement Waterfalls, and Cohort Net Revenue Retention (NRR) matrices.

---

## 🛠️ Key Project Requirements

### Requirement 1: Data Hygiene & Point-in-Time FX Conversion
- Impute missing `currency` values based on each customer's most frequent known currency (defaulting to `'USD'` if unknown).
- Standardize all `plan_mrr` amounts into **USD** using point-in-time daily exchange rates (`fx_rates`).
- Perform vectorized point-in-time matching using `pd.merge_asof` to align event timestamps with exact rate dates without using slow loops.

### Requirement 2: Sequence Reconstruction & Monthly State Snapshot
- Re-order asynchronous, out-of-order event logs chronologically across distributed servers.
- Reconstruct the true end-of-month MRR state for every customer across all 12 calendar months (`2025-01` to `2025-12`).
- Carry forward active MRR states for inactive months and default pre-signup states to `$0`.

### Requirement 3: Categorized MRR Waterfall Engine
Categorize month-over-month revenue movements ($M-1 \to M$) strictly into 5 financial classifications:
1. **New MRR:** First-time active customer ($0 \to >0$).
2. **Expansion MRR:** Active customer increasing their monthly contract value.
3. **Contraction MRR:** Active customer reducing contract value while remaining active ($>0$).
4. **Churn MRR:** Active customer dropping to `$0` MRR.
5. **Reactivation MRR:** Previously churned customer returning to positive MRR.

### Requirement 4: Net Revenue Retention (NRR) Matrix
Compute the 6-month Cohort Net Revenue Retention Matrix to measure organic expansion vs. churn:
$$\text{NRR}_{c, t} = \frac{\text{Total USD MRR of Cohort } c \text{ in Month } t}{\text{Initial Starting USD MRR of Cohort } c \text{ at Month } 0} \times 100$$

---

## ⚙️ Tech Stack & Analytical Methods
- **Language:** Python 3.10+
- **Core Libraries:** `pandas`, `numpy`
- **Key Concepts:** Time-Series Analysis, Dynamic FX Joins (`pd.merge_asof`), Grouped Windowing, Matrix Reshaping/Pivoting, SaaS Financial Modeling.

---

## 📂 Project Structure
```text
├── subscription_events.csv    # Raw asynchronous subscription event logs
├── fx_rates.csv               # Daily FX exchange rates (USD base)
├── generate_data.py           # Synthetic dataset generator
├── mrr_engine.py              # Main analytics & calculation engine
└── README.md                  # Project documentation
