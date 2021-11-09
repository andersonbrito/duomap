import pandas as pd
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Normalize data matrix, against another matrix or using constant, fixed values",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--input1", required=True, help="Main matrix, used as the numerator")
    parser.add_argument("--input2", required=True, type=str,  help="Secondary matrix, with values used as denominators")
    parser.add_argument("--index", required=True, type=str,  help="Column with unique identifiers in both matrices")
    parser.add_argument("--norm-var", required=False, type=str,  help="Single column to be used for normalization of all columns (e.g. population)")
    parser.add_argument("--rate", required=False, type=int,  help="Rate factor for normalization (e.g. 100000 habitants)")
    parser.add_argument("--output", required=True, help="TSV matrix with normalized values")
    args = parser.parse_args()


    input1 = args.input1
    input2 = args.input2
    index = args.index
    norm_variable = args.norm_var
    rate_factor = args.rate
    unique_id = args.index
    output = args.output


    # path = '/Users/anderson/GLab Dropbox/Anderson Brito/ITpS/projetos_itps/dashboard/bimap/pipeline/data/'
    # input1 = path + 'matrix_brazil-states_deaths_months.tsv'
    # input2 = path + 'population_states.tsv'#'matrix_brazil-states_cases_months.tsv'#
    # unique_id = 'state'
    # norm_variable = 'population'
    # rate_factor = 100000
    # output = path + 'matrix_brazil-states_deaths100k'

    def load_table(file):
        df = ''
        if str(file).split('.')[-1] == 'tsv':
            separator = '\t'
            df = pd.read_csv(file, encoding='utf-8', sep=separator, dtype='str')
        elif str(file).split('.')[-1] == 'csv':
            separator = ','
            df = pd.read_csv(file, encoding='utf-8', sep=separator, dtype='str')
        elif str(file).split('.')[-1] in ['xls', 'xlsx']:
            df = pd.read_excel(file, index_col=None, header=0, sheet_name=0, dtype='str')
            df.fillna('', inplace=True)
        else:
            print('Wrong file format. Compatible file formats: TSV, CSV, XLS, XLSX')
            exit()
        return df

    # open dataframe
    df = load_table(input1)
    df.fillna('', inplace=True)

    df2 = load_table(input2)
    df2.fillna('', inplace=True)

    # print(df.head)
    # print(df2.head)
    # print(df2.columns.tolist())

    # get columns
    date_columns = []
    for column in df.columns.to_list():
        if column[-1].isdecimal():
            if norm_variable in ['', None]:
                if column in df2.columns.tolist():
                    date_columns.append(column)
            else:
                date_columns.append(column)

    # create empty dataframes
    nondate_columns = [column for column in df.columns.to_list() if column not in date_columns]
    df3 = df.filter(nondate_columns, axis=1)

    # set new index
    df.set_index(unique_id, inplace=True)
    df2.set_index(unique_id, inplace=True)
    df3.set_index(unique_id, inplace=True)
    # print(df3)

    # perform normalization
    for idx, row in df.iterrows():
        # print('\n' + str(idx))
        for time_col in date_columns:
            numerator = int(df.loc[idx, time_col])
            if norm_variable in ['', None]:
                denominator = int(df2.loc[idx, time_col])
            else:
                denominator = int(df2.loc[idx, norm_variable])

            if denominator == 0: # prevent division by zero
                normalized = 0
            else:
                if norm_variable in ['', None]:
                    normalized = numerator / denominator
                else:
                    if rate_factor in ['', None]:
                        rate_factor = 1
                        print('\nNo rate factor provided. Using "1" instead.')
                    normalized = (numerator * rate_factor) / denominator

            # print(numerator, denominator)
            # print(normalized)
            df3.at[idx, time_col] = normalized

    # print(df3.head)

    df3 = df3.reset_index()
    # print(df3)

    # output converted dataframes
    df3.to_csv(output, sep='\t', index=False)
    print('\nNormalization successfully completed.\n')