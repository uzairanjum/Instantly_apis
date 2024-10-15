import pandas as pd

# Load both CSV files
csv1 = pd.read_csv('contacted.csv')
csv2 = pd.read_csv('uww.csv')

# Create a new column in both CSVs that combines 'First Name' and 'Last Name'
csv1['full_name'] = csv1['First Name'] + ' ' + csv1['Last Name']
csv2['full_name'] = csv2['First Name'] + ' ' + csv2['Last Name']

# Add a new column "contacted" in csv2, and mark "Yes" if the full name exists in csv1
csv2['contacted'] = csv2['full_name'].apply(lambda x: 'Yes' if x in csv1['full_name'].values else 'No')

# Drop the temporary 'full_name' column if you don't need it in the final output
csv2.drop('full_name', axis=1, inplace=True)

# Save the updated csv2 to a new file
csv2.to_csv('All UW Updated.csv', index=False)

print("CSV2 updated successfully.")