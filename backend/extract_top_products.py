import pandas as pd

file_path = 'data/train.csv'
out_path = 'data/train_top1000.csv'

def main():
    print("Calculating item sales in chunks...")
    item_sales = {}
    chunksize = 2_000_000
    for chunk in pd.read_csv(file_path, usecols=['item_nbr', 'unit_sales'], chunksize=chunksize):
        # Fill NaN if any, though Favorita data usually doesn't have NaN unit_sales
        chunk['unit_sales'] = chunk['unit_sales'].fillna(0)
        sales = chunk.groupby('item_nbr')['unit_sales'].sum()
        for item, s in sales.items():
            item_sales[item] = item_sales.get(item, 0) + s

    # Sort and get top 1000
    top_items = sorted(item_sales.items(), key=lambda x: x[1], reverse=True)[:1000]
    top_item_set = set(item[0] for item in top_items)
    print(f"Found top 1000 items. Top item {top_items[0][0]} has {top_items[0][1]} sales.")
    print(f"Bottom item {top_items[-1][0]} has {top_items[-1][1]} sales.")

    print("Extracting rows for top 1000 items...")
    with open(out_path, 'w', newline='') as f_out:
        first_chunk = True
        for chunk in pd.read_csv(file_path, chunksize=chunksize):
            filtered = chunk[chunk['item_nbr'].isin(top_item_set)]
            filtered.to_csv(f_out, index=False, header=first_chunk)
            first_chunk = False

    print("Done extracting to train_top1000.csv!")

if __name__ == '__main__':
    main()
