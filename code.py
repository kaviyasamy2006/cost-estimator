import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from rich.console import Console
from rich.table import Table
from termcolor import colored
import random
import sys

console = Console()

# -------------------------
# Load Hospital Dataset (path must be correct)
# -------------------------
file_path = "/content/dataset(1).xlsx"  # update path if needed
hospital_df = pd.read_excel(file_path)

# normalize column names
hospital_df.columns = hospital_df.columns.str.strip().str.lower()

# required columns
expected_cols = ["hospital name", "best_treatments", "city", "hospital _type"] # Expect 'hospital _type'
missing = [c for c in expected_cols if c not in hospital_df.columns]
if missing:
    raise ValueError(f"Missing required columns in Excel file: {missing}")

# Rename 'hospital _type' to 'hospital_type' if it exists
if 'hospital _type' in hospital_df.columns:
    hospital_df.rename(columns={'hospital _type': 'hospital_type'}, inplace=True)

# ensure columns are strings (so .str works) and remove leading/trailing whitespace
hospital_df["best_treatments"] = hospital_df["best_treatments"].fillna("").astype(str).str.strip()
hospital_df["city"] = hospital_df["city"].fillna("").astype(str).str.strip()
hospital_df["hospital_type"] = hospital_df["hospital_type"].fillna("").astype(str).str.strip()

# -------------------------
# Treatment cost table (with ranges)
# -------------------------
treatment_costs = {
    "cold/flu": {"public": (50, 200), "private": (300, 600), "specialty": (800, 1200)},
    "fever": {"public": (50, 250), "private": (300, 600), "specialty": (1000, 1800)},
    "diabetes check-up": {"public": (0, 0), "private": (600, 1200), "specialty": (2500, 4000)},
    "orthopedic": {"public": (5000, 8000), "private": (20000, 25000), "specialty": (35000, 40000)},
    "cardiac": {"public": (70000, 100000), "private": (150000, 200000), "specialty": (300000, 350000)},
    "neurology": {"public": (40000, 60000), "private": (120000, 150000), "specialty": (250000, 300000)},
    "skin allergy": {"public": (100, 300), "private": (600, 2000), "specialty": (3000, 3500)},
    "dental care": {"public": (300, 600), "private": (2000, 2500), "specialty": (4000, 5000)}
}

# -------------------------
# User inputs
# -------------------------
console.print("\n💊 [bold magenta]Medical Cost Prediction & Hospital Recommendation[/bold magenta]")
try:
    name = input("Enter your name: ").strip()
    age = int(input("Enter your age: ").strip())
    bmi = float(input("Enter your BMI: ").strip())
except Exception as e:
    console.print(colored("Invalid numeric input. Please enter valid age and BMI.", "red"))
    sys.exit(1)

gender = input("Enter your gender (Male/Female/Other): ").strip()
smoker = input("Are you a smoker? (yes/no): ").strip().lower()
region = input("Enter your region (north/south/east/west): ").strip().lower()
city = input("Enter your city: ").strip().lower()

print("\nAvailable Treatments:")
for t in treatment_costs.keys():
    print("-", t)
treatment = input("\nSelect treatment: ").strip().lower()
hospital_type = input("Select hospital type (public/private/specialty): ").strip().lower()

# validate treatment and hospital_type
if treatment not in treatment_costs:
    console.print(colored(f"⚠️ Unknown treatment '{treatment}'. Available: {list(treatment_costs.keys())}", "red"))
    sys.exit(1)
if hospital_type not in ("public", "private", "specialty"):
    console.print(colored("⚠️ Invalid hospital type. Choose public/private/specialty.", "red"))
    sys.exit(1)

# -------------------------
# Estimate cost (using range)
# -------------------------
min_base_cost, max_base_cost = treatment_costs[treatment].get(hospital_type, (0, 0))

# Calculate estimated cost as the average of the range
estimated_cost = (min_base_cost + max_base_cost) / 2

# Cost adjustments
if smoker == "yes": estimated_cost += 1000
if bmi > 30: estimated_cost += 500
if age > 60: estimated_cost += 1000

console.print("\n" + "="*60)
console.print(f"👤 Name: [bold cyan]{name}[/bold cyan]")
console.print(f"🏙️ City: [bold green]{city.title()}[/bold green]")
console.print(f"🏥 Hospital Type: [bold yellow]{hospital_type.title()}[/bold yellow]")
console.print(f"💰 Estimated Cost: [bold green]₹{round(estimated_cost,2)}[/bold green]")
console.print(f"💵 Typical Cost Range: [bold green]₹{min_base_cost:,} – ₹{max_base_cost:,}[/bold green]")
console.print("="*60)

# -------------------------
# Recommend nearby hospitals
# -------------------------
# normalize for comparison
treatment_lc = treatment.lower()
city_lc = city.lower()

# Use Series (safe) and lowercase for matching
bt_series = hospital_df["best_treatments"].str.lower()
city_series = hospital_df["city"].str.lower()

mask = bt_series.str.contains(treatment_lc, na=False) & city_series.str.contains(city_lc, na=False)

nearby = hospital_df[mask].copy()

if nearby.empty:
    console.print(colored(f"⚠️ No hospitals found in {city.title()} for '{treatment.title()}'. Showing top hospitals that offer this treatment:", "yellow"))
    nearby = hospital_df[bt_series.str.contains(treatment_lc, na=False)].copy()

# create display column with hospital type in brackets
# Ensure 'hospital_type' column exists before using it
if 'hospital_type' in nearby.columns:
    nearby["hospital_info"] = nearby.apply(
        lambda r: f"{r['hospital name']} ({r['hospital_type'].title()})", axis=1
    )
else:
    # Fallback if renaming failed for some reason (shouldn't happen with fix)
     nearby["hospital_info"] = nearby.apply(
        lambda r: f"{r['hospital name']}", axis=1
    )


# limit results and reset index for neat numbering
nearby_display = nearby[["hospital_info", "city"]].reset_index(drop=True).head(10)

# display using rich table
table = Table(show_header=True, header_style="bold blue")
table.add_column("No.", style="dim", width=4)
table.add_column("Hospital", style="bold magenta")
table.add_column("City", style="green")

for idx, row in nearby_display.iterrows():
    table.add_row(str(idx+1), row["hospital_info"], row["city"].title())

console.print(table)

# -------------------------
# Visualize cost comparison (using average for bar chart)
# -------------------------
plt.figure(figsize=(8, 5))
# Calculate average cost for visualization
avg_cost_data = {k: (v[0] + v[1]) / 2 for k, v in treatment_costs[treatment].items()}
sns.barplot(x=list(avg_cost_data.keys()), y=list(avg_cost_data.values()), palette="coolwarm")
plt.title(f"💰 Average Cost Comparison for {treatment.title()}")
plt.xlabel("Hospital Type")
plt.ylabel("Cost (₹)")
plt.grid(True, linestyle="--", alpha=0.7)
plt.show()


console.print("\n🎉 [bold green]Completed![/bold green]")

