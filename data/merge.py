import os
import pandas as pd

def merge_csv_files(input_dir, output_file):
    csv_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.csv')]

    print(f"{len(csv_files)} CSV file(s) in '{input_dir}'. Starting merge...")

    df_list = []

    for file in csv_files:
        file_path = os.path.join(input_dir, file)
        df = pd.read_csv(file_path)
        df_list.append(df)
        print(f"read '{file}'.")

    merged_df = pd.concat(df_list, ignore_index=True)
    merged_df.to_csv(output_file, index=False)
    print(f"CSV files have been merged into '{output_file}'.")


if __name__ == "__main__":
    input_directory = './'

    # output file path
    output_csv = '../data.csv'

    merge_csv_files(input_directory, output_csv)
