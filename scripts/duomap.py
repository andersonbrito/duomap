import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import argparse

pd.set_option('display.max_columns', 500)
font = {'family': 'Arial', 'weight': 'regular', 'size': 8}
matplotlib.rc('font', **font)

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(
    #     description="Pairwise association between corresponding columns and rows in two matrices, generating stacked rows with data",
    #     formatter_class=argparse.ArgumentDefaultsHelpFormatter
    # )
    # parser.add_argument("--input1", required=True, help="Matrix with data to be displayed in the X axis")
    # parser.add_argument("--input2", required=True, help="Matrix with data to be displayed in the Y axis")
    # parser.add_argument("--index", required=True, help="Column with unique identifier, common to both matrices")
    # parser.add_argument("--xvar", required=True, type=str,  help="Name of the variable X")
    # parser.add_argument("--yvar", required=True, type=str,  help="Name of the variable Y")
    # parser.add_argument("--extra-columns", required=False, nargs='+', type=str,
    #                     help="Extra columns with geographic info to export")
    # parser.add_argument("--output", required=True, help="TSV file showing corrected genome counts per epiweek")
    # args = parser.parse_args()


    path = '/Users/anderson/GLab Dropbox/Anderson Brito/ITpS/projetos_itps/dashboard/nextstrain/run8_20211029_itps5/data/'
    input = path + 'stacked_matrix.tsv'
    config = path + 'config_single.tsv'
    # output = path + input.split('/')[-1].split('.')[0] + '_categories.tsv'

    # xvar = 'cases_100k'
    # # xvar_bins = [50, 200, 500, 20000]
    # xvar_bins = [100, 500, 20000]
    #
    # yvar = 'proportion_seq'
    # # yvar_bins = [0.001, 0.005, 0.01, 5]
    # yvar_bins = [0.001, 0.005, 5]
    #
    # id_geocol = 'ADM1_PCODE'
    # id_datacol = 'ADM_code'
    #
    # legend_type = 'separate'
    # show_legend = 'yes'
    #
    # # plot dimensions
    # plot_width = 10
    # plot_heigth = 8


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


    # Load sample metadata
    df1 = load_table(input)
    df1.fillna('0', inplace=True)

    params = load_table(config)
    params.fillna('', inplace=True)
    params = params.set_index('param')
    # print(params)

    id_geocol = params.loc['unique_id1', 'value']
    id_datacol = params.loc['unique_id2', 'value']

    map_type = params.loc['map_type', 'value']

    xvar = params.loc['xvar', 'value']
    xvar_bins = [float(bound) for bound in params.loc['xbins', 'value'].split(',')]

    if map_type == 'bivariate':
        yvar = params.loc['yvar', 'value']
        yvar_bins = [float(bound) for bound in params.loc['ybins', 'value'].split(',')]

    show_legend = params.loc['legend', 'value']

    # plot dimensions
    plot_width = int(params.loc['figsize', 'value'].split(',')[0].strip())
    plot_heigth = int(params.loc['figsize', 'value'].split(',')[1].strip())

    # filter
    filters = params.loc['filter', 'value']
    df2 = pd.DataFrame()
    if filters not in ['', None]:
        for filter_value in sorted(filters.split(',')):
            filter_value = filter_value.strip()
            if not filter_value.startswith('~'):
                df_filtered = df1[df1[filter_value.split(':')[0]].isin([filter_value.split(':')[1]])]
                df2 = df2.append(df_filtered)
                # df2 = df1

        for filter_value in sorted(filters.split(',')):
            filter_value = filter_value.strip()
            if filter_value.startswith('~'):
                filter_value = filter_value[1:]
                if df2.empty:
                    df1 = df1[~df1[filter_value.split(':')[0]].isin([filter_value.split(':')[1]])]
                    df2 = df2.append(df1)
                else:
                    df2 = df2[~df2[filter_value.split(':')[0]].isin([filter_value.split(':')[1]])]
    else:
        df2 = df1

    labels_x = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
    labels_y = ['A', 'B', 'C', 'D', 'E', 'F']

    # hexcolours = ["#d3d3d3", "#cca0a0", "#c5696a", "#ba1a1c", "#9cbdcf", "#96909d", "#915e67", "#89181c", "#60a6ca", "#5d7e99", "#5a5365", "#55151b", "#1e8dc5", "#1d6b96", "#1c4663", "#1a121a"]
    # hexcolours = ["#d3d3d3", "#c49494", "#b25050", "#79b0c7", "#707b8c", "#66434c", "#1288ba", "#115f82", "#0f3346"]
    # notfoundcolour = '#FFFFFF'

    hexcolours = [hex.strip() for hex in params.loc['colours', 'value'].replace('"','').split(',')]
    notfoundcolour = params.loc['missing_colour', 'value']


    colour_scheme = {}
    c = 0
    if map_type == 'bivariate':
        for y in labels_y[:len(yvar_bins)]:
            for x in labels_x[:len(xvar_bins)]:
                label = y + x
                colour_scheme[label] = hexcolours[c]
                c += 1
    else:
        for x in labels_x[:len(xvar_bins)]:
            label = x
            colour_scheme[label] = hexcolours[c]
            c += 1

    ticks = []
    def classify(df, column, bins, axis):
        bins = [0] + bins
        # print(bins)
        for idx, row in df.iterrows():
            value = float(df.loc[idx, column])
            for num, varbin in enumerate(bins):
                # print(num, len(bins) - 1)
                if num < len(bins) - 1:
                    start, end = bins[num], bins[num + 1]
                    # print(bins[num], bins[num + 1])
                    tick_label = str(start) + '-' + str(end)
                    if tick_label not in ticks:
                        ticks.append(tick_label)
                    if start < value <= end:
                        # print(start, '<', value, '<', end, labels_x[num])
                        if axis == 'x':
                            df.loc[idx, 'x_category'] = labels_x[num]
                        else:
                            df.loc[idx, 'y_category'] = labels_y[num]

    # add x and y categories
    classify(df2, xvar, xvar_bins, 'x')
    if map_type == 'bivariate':
        classify(df2, yvar, yvar_bins, 'y')
        df2['category'] = df2['y_category'].astype(str) + df2['x_category'].astype(str)
    else:
        df2['category'] = df2['x_category'].astype(str)

    # output converted dataframes
    output = params.loc['output_file', 'value']
    if output not in ['', None]:
        df2.to_csv(output, sep='\t', index=False)
    df2.set_index(id_datacol, inplace=True)


    # shapefiles
    shape1_path = params.loc['shape1', 'value']
    geodf = gpd.read_file(shape1_path)
    shape2_path = params.loc['shape2', 'value']
    if shape2_path not in ['', None]:
        shape2_path = params.loc['shape2', 'value']
        geodf2 = gpd.read_file(shape2_path)

    # geodf = gpd.read_file('/Users/anderson/GLab Dropbox/Anderson Brito/codes/geoCodes/bra_adm_ibge_2020_shp/bra_admbnda_adm2_ibge_2020.shp')
    # geodf = gpd.read_file('/Users/anderson/GLab Dropbox/Anderson Brito/codes/geoCodes/bra_adm_ibge_2020_shp/bra_admbnda_adm1_ibge_2020.shp')
    # print(geodf['cd_hlt_'].tolist())

    # plot specifications
    nrows = int(params.loc['nrows', 'value'])
    ncols = int(params.loc['ncols', 'value'])

    figsize = (plot_width, plot_heigth)#[int(value.strip()) for value in params.loc['figsize', 'value'].split(',')]
    fig, axes = plt.subplots(nrows, ncols, sharex=True, sharey=True, figsize=figsize)

    column = params.loc['groupby', 'value']

    # table legend
    cells = []
    legend_hex = []
    for b in reversed(range(len(xvar_bins))):
        cells.append(list(colour_scheme.keys())[b*len(xvar_bins):b*len(xvar_bins)+len(xvar_bins)])
        legend_hex.append(list(colour_scheme.values())[b*len(xvar_bins):b*len(xvar_bins)+len(xvar_bins)])

    cells = [l for l in cells if len(l) > 0]
    legend_hex = [l for l in legend_hex if len(l) > 0]

    for i, (name, df) in enumerate(df2.groupby(column)):
        # print(i, name, df)
        # define plot limits

        upperleft_coord = [float(value.strip()) for value in params.loc['upperleft_coord', 'value'].split(',')]
        lowerright_coord = [float(value.strip()) for value in params.loc['lowerright_coord', 'value'].split(',')]

        # upperleft_coord = [6.229315338733764, -75.54160920146641]
        # lowerright_coord = [-34.29680185909136, -32.66581314238647]

        xlim = ([upperleft_coord[1], lowerright_coord[1]])
        ylim = ([lowerright_coord[0], upperleft_coord[0]])

        if nrows >= 2 and ncols >= 2:#nrows + ncols > 3:
            # print(i // ncols, i % ncols)
            ax = axes[i // ncols][i % ncols]
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
        elif nrows < 2 or ncols < 2:
            # print(i // ncols, i % ncols)
            ax = axes[i]
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)


        # print('\n' + name)
        for shape, data in geodf.groupby(id_geocol):
            shape = str(shape)
            # print(shape)
            # define the color for each group using the dictionary
            if shape in df.index:
                value = df.loc[shape, 'category']
            else:
                value = 'NA'


            if value in colour_scheme:
                colour = colour_scheme[value]
            else:
                colour = notfoundcolour

            # ax.axis('off')

            # Plot each group using the color defined above
            data.plot(color=colour,
                      ax=ax,
                      edgecolor='#858585',
                      linewidth=0.25,
                      label=value)
            ax.set_axis_off()
        if shape2_path not in ['', None]:
            geodf2.plot(ax=ax, color='none', edgecolor='black', linewidth=0.5)

        # label
        ax.text(upperleft_coord[1] + 0.05, upperleft_coord[0] + 1,
        s=name, horizontalalignment='left', fontsize=10, color='#000000', zorder=30)

        # table legend
        axins = ax.inset_axes([-0.2, -0.1, 0.6, 0.6])
        axins.axis('tight')
        axins.axis('off')

        if map_type == 'bivariate':
            counts = df['category'].value_counts().to_dict()
            newdata = []
            for row in cells:
                new_row = []
                for cat in row:
                    if cat in counts:
                        new_row.append(counts[cat])
                    else:
                        new_row.append('-')
                newdata.append(new_row)

            table = axins.table(cellText=newdata, cellLoc='center', loc="center",
                                colWidths=[0.1 for x in range(len(xvar_bins))], fontsize=6)

            # height_map = abs(upperleft_coord[0] - lowerright_coord[0])
            table.scale(1, plot_heigth / (nrows * 4))

            for key, cell in table.get_celld().items():
                cell.set_linewidth(0.2)

    # These are in unitless percentages of the figure size. (0,0 is bottom left)
    # left, bottom, width, height = [0, 0, 0, 0]
    # ax2 = fig.add_axes([left, bottom, width, height])

    add_legend = False
    if str(params.loc['legend', 'value']).lower() == 'true':
        add_legend = True

    if add_legend == True:
        if nrows >= 2 and ncols >= 2:
            ax = axes[nrows-1][ncols-1]
        else:
            ax = axes[-1]

        ax.axis('tight')
        ax.axis('off')

    if map_type == 'bivariate':
        table = ax.table\
            (cellText=cells, cellColours=legend_hex, cellLoc='center', loc="center",
            rowLabels=ticks[:len(xvar_bins)][::-1], colLabels=ticks[len(xvar_bins):],
            colWidths=[0.15 for x in range(len(xvar_bins))], fontsize=8)
        table.scale(1, plot_heigth / (nrows * 1.5))
    else:
        table = ax.table\
            (cellText=cells, cellColours=legend_hex, cellLoc='center', loc="center",
            colLabels=ticks, colWidths=[0.15 for x in range(len(xvar_bins))], fontsize=8)
        table.scale(1, plot_heigth / (nrows * 1.5))
    plt.show()


