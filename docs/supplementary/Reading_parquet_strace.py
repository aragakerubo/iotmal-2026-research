import pyarrow.parquet as pq
import pandas as pd

# === Step 1: Open merged parquet file ===
url = '/content/drive/MyDrive/CICYoKMal/New/x86/preprocessed_strace.parquet'
parquet_file = pq.ParquetFile(url)

# === Step 2: Collect all columns across batches ===
all_cols = set()
for i in range(parquet_file.num_row_groups):
    batch_df = parquet_file.read_row_group(i).to_pandas()
    all_cols |= set(batch_df.columns)

all_cols = list(all_cols)  # final union of columns

# === Step 3: First pass – compute sums and counts for numeric columns ===
sums = None
counts = None
numeric_cols = None

for i in range(parquet_file.num_row_groups):
    batch_df = parquet_file.read_row_group(i).to_pandas()
    batch_df = batch_df.reindex(columns=all_cols)

    numeric_cols = batch_df.select_dtypes(include=['number']).columns
    if sums is None:
        sums = pd.Series(0.0, index=numeric_cols)
        counts = pd.Series(0, index=numeric_cols)

    sums += batch_df[numeric_cols].sum(skipna=True)
    counts += batch_df[numeric_cols].count()

means = sums / counts  # global means

# === Step 4: Second pass – fill NaNs batch by batch ===
dfs = []
for i in range(parquet_file.num_row_groups):
    batch_df = parquet_file.read_row_group(i).to_pandas()
    batch_df = batch_df.reindex(columns=all_cols)
    batch_df[numeric_cols] = batch_df[numeric_cols].fillna(means)
    dfs.append(batch_df)

# === Step 5: Final merged DataFrame ===
merged_df_strace = pd.concat(dfs, ignore_index=True)

# Save back to parquet
# merged_df_strace.to_parquet("./dataset_sampled_cleaned.parquet", engine='pyarrow', index=False)

# Count occurrences
counts = merged_df_strace["MalwareFamily"].value_counts()

# Calculate percentages
percentages = counts / counts.sum() * 100

# Combine into a DataFrame
result = pd.DataFrame({
    "MalwareFamily": counts.index,
    "Count": counts.values,
    "%": percentages.values.round(2)  # round to 2 decimals
})

# Print dataset info
print("Dataset shape:", merged_df.shape)
print("\nClass distribution (excluding 'unknown'):\n")
print(result.to_string(index=False))