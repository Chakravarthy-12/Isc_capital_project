import warnings

import pandas as pd

m_dataframe = pd.read_csv('m.csv')
m_dataframe.sort_values(by=['EndOfWeek', 'WorkDate'], inplace=True)
# Reset the index of the sorted DataFrame
m_dataframe.reset_index(drop=True, inplace=True)
filter_df = m_dataframe[m_dataframe['Pay'] == "Hourly"]
non_hourly_df = (m_dataframe[~m_dataframe.index.isin(filter_df.index)]).sort_values(by=['Pay', 'WorkDate'],
                                                                                    ascending=[False, True])
STANDARD_WORK_HRS = 40
pivot_df = filter_df.groupby(['EndOfWeek', 'Employee'])['Hour'].sum().reset_index()

# Get the employee details working more than 40 hours in a particular week and job
overtime_employees = pivot_df[pivot_df['Hour'] > STANDARD_WORK_HRS].copy()
if overtime_employees.empty:
    print("No overtime employees found.")
    m_dataframe.to_csv('m.csv', index=False)  # convert this folder and format for your convenience
else:
    # Initialize overtime df with correct columns
    overtime_df = pd.DataFrame(columns=filter_df.columns)

    # Loop through every employee working more than 40 hours
    for _, employee in overtime_employees.iterrows():
        try:
            matched_rows = filter_df[
                (filter_df['EndOfWeek'] == employee['EndOfWeek']) &
                (filter_df['Employee'] == employee['Employee'])
                ].copy()
            matched_rows['CumulativeHours'] = matched_rows['Hour'].cumsum()
            # Find index where cumulative hours exceed standard work hours
            change_at = matched_rows.loc[matched_rows['CumulativeHours'] > STANDARD_WORK_HRS].index[0]

            # Calculate standard work hours before change index
            sum_of_hrs_before_exceeds = matched_rows.loc[:change_at - 1, 'Hour'].sum()

            if sum_of_hrs_before_exceeds != STANDARD_WORK_HRS:
                # Adjust working hours up to standard work hours
                std_work_hr = STANDARD_WORK_HRS - sum_of_hrs_before_exceeds
                matched_rows.loc[change_at, 'Hour'] = std_work_hr  # ROUND OFF TO 40

                # Create new row with remaining hours at certain index
                new_row = matched_rows.loc[change_at].copy()
                remaining_hours = new_row['CumulativeHours'] - STANDARD_WORK_HRS
                new_row['Hour'] = remaining_hours
                new_row['Pay'] = 'Hourly - Overtime'
                del new_row['CumulativeHours']
                new_row_df = pd.DataFrame([new_row.values], columns=new_row.index)

                # Append new_row to overtime_df
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=FutureWarning)
                    overtime_df = pd.concat([overtime_df, new_row_df], axis=0, ignore_index=True)

                # Update Pay for remaining hours as overtime
                matched_rows.loc[change_at + 1:, 'Pay'] = 'Hourly - Overtime'
            else:
                matched_rows.loc[change_at:, 'Pay'] = 'Hourly - Overtime'

            matched_rows.drop(columns='CumulativeHours', inplace=True)
            filter_df.loc[matched_rows.index] = matched_rows.values
        except (IndexError, KeyError) as e:
            print(f"Error in adjusting work hours and pay: {e}")

    combined_df = pd.concat([filter_df, overtime_df], ignore_index=True)
    combined_df.sort_values(by=['EndOfWeek', 'WorkDate'], inplace=True)
    # Non-hourly dataframe appending in last
    combined_df = pd.concat([combined_df, non_hourly_df], ignore_index=True)
    combined_df.to_excel('final_output.xlsx', engine='openpyxl', index=False)

    # If non-hourly dataframe also concatenate basis on week Date Uncomment below lines and command the above 4 lines
    # combined_df = pd.concat([filter_df, overtime_df, non_hourly_df], ignore_index=True)
    # combined_df.sort_values(by=['EndOfWeek', 'WorkDate'], inplace=True)
    # combined_df.to_excel('final_output.xlsx', engine='openpyxl', index=False)
