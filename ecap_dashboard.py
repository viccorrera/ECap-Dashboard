import pandas as pd
import numpy as np
import os
from os import listdir
from dateutil.relativedelta import relativedelta

def get_path(file_name):
        """Return the full path of file_name 
        inside 'Data' folder.

        Parameters
        ---------- 
        """
        
        content_list = listdir(os.path.join(os.getcwd(), 'Data'))
        file_path = os.path.join(
            os.getcwd(),
            'Data',
            list(filter(lambda x: file_name in x, content_list))[0]
        )

        return file_path


def import_file(path : str, dtypes : dict, usecols=None):
    """Import .txt files only.
    """     
    df = pd.read_csv(
        path,
        sep='\t',
        dtype=dtypes,
        usecols=usecols
    )
    
    return df

cedant_names_dtype = {
    'Cedant': str,
    'Comp': str
}

so_reporting_dtype = {
    'CUSTOMER_ID': str,
    'ALIAS_ID': str,
    'ULTIMATE_ID': str
}

treaty_reg_dtype = {
    'Comp': str,
    'Seq': str,
    'UW Yr': str
}
        

class UnratedADV:
    """Class that produces the Unrated and Adverse buyers
    Spreadsheet.
    """

    def __init__(self, this_quarter_file_path):
        self.this_quarter_raw = import_file(
            path=this_quarter_file_path,
            dtypes=so_reporting_dtype
        )
        self.buyer_info = self.buyer_info_df()
    
    def buyer_info_df(self):
        "Generate DataFrame with buyers' information"
        df = self.this_quarter_raw[[
            'ULTIMATE_ID',
            'ULTIMATE_NAME',
            'ULTIMATE_ISO_COUNTRY'
        ]].copy()
        
        return df.drop_duplicates('ULTIMATE_ID')
    
    @staticmethod
    def insert_treaty_id_count_col(dataframe):
        df = dataframe.copy()

        df['NUMBER_OF_TREATIES'] = 0

        uniques_combo = df.duplicated(subset=['CONTRACT_ID', 'ULTIMATE_ID'])
        
        # Assign 1 to unique ['CONTRACT_ID', 'ULTIMATE_ID']
        df.loc[(~uniques_combo), 'NUMBER_OF_TREATIES'] = 1

        return df


    def generate_top_unrated_buyers(self, n_buyer):
        """Generate list of top unrated buyers
        
        Parameters
        ----------
        n_buyers : int
            Number of top buyers to include in list
        """

        df = self.this_quarter_raw.copy()

        df = self.insert_treaty_id_count_col(df)
        
        # Both conditions are according to SQL statements
        cond_1 = df['ULTIMATE_RATING_TYPE'].isna()
        cond_2 = df['MODEL_SUB_TYPE'].isin([
            'CI_COM_UNK',
            'BO_COM_UNK',
            'CI_POL_KN',
            'CI_POL_UNK'
        ])
        
        df_filtered = df.loc[(cond_1) & (~cond_2)]
        df_group_by_ID = df_filtered.groupby('ULTIMATE_ID').sum().reset_index()
        
        # Only top Exposures
        df_sorted = df_group_by_ID.sort_values(
            'CREDIT_LIMIT_NET_EXPOSURE',
            ascending=False
        ).head(n_buyer)

        df_with_buyer_info = df_sorted.merge(self.buyer_info, how='left')

        df_with_buyer_info = df_with_buyer_info[[
            'ULTIMATE_NAME',
            'ULTIMATE_ID',
            'NUMBER_OF_TREATIES',
            'CREDIT_LIMIT_NET_EXPOSURE'
        ]]

        return df_with_buyer_info
    
    def generate_top_adverse_buyers(self, n_buyer):
        """Generate list of top adverse buyers
        
        Parameters
        ----------
        n_buyers : int
            Number of top buyers to include in list
        """
        df = self.this_quarter_raw

        df = self.insert_treaty_id_count_col(df)

        # Helper column for calculating Cedant PD
        df['Step_1_Cedant_PD'] = (
            df['CREDIT_LIMIT_NET_EXPOSURE'] 
            * df['ULTIMATE_POD']
        )

        # Both conditions are according to SQL statements
        cond_1 = df['ULTIMATE_RATING_TYPE'] == 'ADV'
        cond_2 = df['MODEL_SUB_TYPE'].isin([
            'CI_COM_UNK',
            'BO_COM_UNK',
            'CI_POL_KN',
            'CI_POL_UNK'
        ])

        df_filtered = df.loc[(cond_1) & (~cond_2)]

        df_group_by_ID = df_filtered.groupby('ULTIMATE_ID').sum().reset_index()

        df_group_by_ID['PD'] = (
            df_group_by_ID['Step_1_Cedant_PD'] 
            / df_group_by_ID['CREDIT_LIMIT_NET_EXPOSURE']
        )

        df_group_by_ID.drop('Step_1_Cedant_PD', axis=1, inplace=True)

        # Only top Exposures
        df_sorted = df_group_by_ID.sort_values(
            'CREDIT_LIMIT_NET_EXPOSURE',
            ascending=False
        ).head(n_buyer)

        df_with_buyer_info = df_sorted.merge(self.buyer_info, how='left')

        df_with_buyer_info = df_with_buyer_info[[
            'ULTIMATE_NAME',
            'ULTIMATE_ID',
            'ULTIMATE_ISO_COUNTRY',
            'NUMBER_OF_TREATIES',
            'CREDIT_LIMIT_NET_EXPOSURE'
        ]]

        return df_with_buyer_info


class SOReporting:
    def __init__(
        self,
        product_type,
        period,
        reporting_date
        ):
        """Initiates Master class for the ECap Dashboard.

        Parameters
        ----------
        product_type : str
            'bond' or 'credit'
        period : str
            'Old' or 'New', with first letter Uppercase
        reporting_date : str. Converts to Pandas.DateTime
            'dd/mm/yyyy'
        """
        self.product_type = product_type
        self.period = period
        self.reporting_date = pd.to_datetime(reporting_date, dayfirst=True)
        self.raw_reporting = self.import_raw_reporting()
        self.register = self.import_register()
    
    def _get_quarter_file(self, file_name):
        """Return the full path of file_name 
        inside 'New' or 'Old' folder.

        Parameters
        ---------- 
        """
        
        content_list = listdir(os.path.join(os.getcwd(), 'Data', self.period))
        file_path = os.path.join(
            os.getcwd(),
            'Data',
            self.period,
            list(filter(lambda x: file_name in x, content_list))[0]
        )

        return file_path

    def import_raw_reporting(self):
        df = pd.read_csv(
            self._get_quarter_file('REPORTING'),
            sep='\t',
            dtype=so_reporting_dtype
        )
        return df
    
    def get_raw_reporting(self):
        return self.raw_reporting

    def import_register(self):
        df = pd.read_csv(
            self._get_quarter_file('TREATYREG'),
            sep='\t',
            skipfooter=1,
            dtype=treaty_reg_dtype,
            usecols=['Comp',
                     'Seq',
                     'UW Yr',
                     'Pd Beg',
                     'Pd End',
                     'Type/Form',
                     'UPR',
                     'EPI is Rev EPI or EPI']
        )

        return df
    
    def get_register(self):
        return self.register

    def get_grouped_by_contract(self):
        df = SOReporting.groupByContract(
            register=self.register,
            raw_reporting=self.raw_reporting,
            product_type=self.product_type,
            reporting_date=self.reporting_date
        ).grouped_by_contract
        
        return df
    
    def get_grouped_by_cedant(self):
        df = SOReporting.groupByCedant(
            dataframe=self.get_grouped_by_contract()
        ).get_grouped_by_cedant()
        
        return df
    
    def get_final_grouped_by_cedant(self):
        df = SOReporting.groupByCedant(
            dataframe=self.get_grouped_by_contract()
        ).get_final_table_by_cedant()
        return df
    

    class groupByContract:
        def __init__(
            self,
            register,
            raw_reporting,
            product_type,
            reporting_date
        ):
            self.register = register
            self.raw_reporting = raw_reporting
            self.product_type = product_type
            self.reporting_date = reporting_date
            self.grouped_by_contract = self.get_grouped_by_contract()

        def add_register_cols(self, dataframe):
            """Add Treaty Register columns to dataframe. 
            Dataframe must be grouped by Contract ID (e.g. 09976C1 0320)
            """
            df = self.register
            
            # Date columns to datetime format
            date_cols = ['Pd Beg', 'Pd End']
            for col in date_cols:
                df[col] = pd.to_datetime(df[col], dayfirst=True)
            
            #include trailing zeros to UW Yr and Comp columns
            df['UW Yr'] = df.apply(
                lambda x: '{0:0>2}'.format(x['UW Yr']),
                axis=1
            )
            
            df['Comp'] = df['Comp'].apply(lambda x: '{0:0>5}'.format(x))
            
            df['CONTRACT_ID'] = df['Comp'] + df['Seq'] + df['UW Yr']

            df['Balloon ID'] = df['CONTRACT_ID'].str[0:10]
            
            dataframe_with_register_info = dataframe.merge(
                right=df,
                how='left',
                on='CONTRACT_ID',
            )
            
            return dataframe_with_register_info


        def group_by_contract(self):
            df = self.raw_reporting.copy()
            df.drop('RSQUARED', axis=1, inplace=True)
            
            # Helper column for calculating Contract PD before grouping
            df['PD_step 1'] = (
                df['CREDIT_LIMIT_NET_EXPOSURE'] 
                * df['ULTIMATE_POD']
            )

            if self.product_type == 'bond':
                
                # Select only 'BO_COM_KN' and 'BO_COM_UNK'
                df_filtered = df.loc[
                    (df['MODEL_SUB_TYPE'] == 'BO_COM_KN') 
                    | (df['MODEL_SUB_TYPE'] == 'BO_COM_UNK')
                ]
                
                # Manual correction because SII uses single digit UW Year,
                # and we use double digit (e.g.: '8' != '08')
                df_filtered.loc[
                    df_filtered['CONTRACT_ID'] == '07367B3 258',
                    'CONTRACT_ID'
                ] = '07367B3 2508'

                df_grouped = df_filtered.groupby(by='CONTRACT_ID').sum()
                df_grouped.reset_index(inplace=True)

            elif self.product_type == 'credit':
                # Select only 'CI_COM_KN' and 'CI_COM_UNK' only for
                # 'CREDIT_LIMIT_NET_EXPOSURE', 'ULTIMATE_POD'
                filter_1 = [
                    'CI_COM_KN',
                    'CI_COM_UNK'
                ]

                df_group_1 = df.loc[
                    df['MODEL_SUB_TYPE'].isin(filter_1)
                ].groupby(by='CONTRACT_ID').sum().reset_index()
                
                # Select only columns related to the filter above
                df_group_1 = df_group_1[['CONTRACT_ID',
                                         'CREDIT_LIMIT_NET_EXPOSURE',
                                         'ULTIMATE_POD',
                                         'PD_step 1']]

                filter_2 = [
                    'CI_COM_KN',
                    'CI_COM_UNK',
                    'CI_POL_KN',
                    'CI_POL_UNK'
                ]
                
                df_group_2 = df.loc[
                    df['MODEL_SUB_TYPE'].isin(filter_2)
                ].groupby(by='CONTRACT_ID').sum().reset_index()

                # Select only columns related to the filter above
                df_group_2 = df_group_2[['CONTRACT_ID',
                                         'EXPECTED_LOSS',
                                         'EC_CONSUMPTION_ND',]]

                df_grouped = df_group_1.merge(df_group_2, on='CONTRACT_ID')
                df_grouped = df_grouped[[
                    'CONTRACT_ID',
                    'CREDIT_LIMIT_NET_EXPOSURE',
                    'EXPECTED_LOSS',
                    'EC_CONSUMPTION_ND',
                    'ULTIMATE_POD',
                    'PD_step 1'
                ]]

            
            # Calculate PD for each Contract ID
            df_grouped['PD'] = (
                df_grouped['PD_step 1'] 
                / df_grouped['CREDIT_LIMIT_NET_EXPOSURE']
            )
            
            # Drop helper columnS
            df_grouped.drop(
                ['PD_step 1', 'ULTIMATE_POD'],
                axis=1,
                inplace=True
            )                
            
            df_grouped.reset_index(inplace=True, drop=True)
            
            df_grouped_with_register_info = self.add_register_cols(
                df_grouped
            )
            
            return df_grouped_with_register_info
        
        @staticmethod
        def create_cedant_dict():
            df = import_file(
                path=get_path('Cedant Names'), 
                dtypes=cedant_names_dtype
            )
            
            # Balloon produces file with extra spaces after name
            df['Cedant'] = df['Cedant'].str.strip()
            
            # Keep only the most recent UW Year (keep='last')
            df.drop_duplicates(subset='Comp', keep='last', inplace=True)

            # Create Series to use with Pandas Map function
            df_dict = pd.Series(
                data = df['Cedant'].values,
                index = df['Comp'].values,
                dtype=str
            )
            
            return df_dict

        @staticmethod
        def insert_cedant_name(dataframe, cedant_name_dict):
            
            df = dataframe
            
            # COMP column used to map Cedants' Names
            df.insert(
                loc=1,
                column='COMP',
                value=df['CONTRACT_ID'].str[0:5]
            )
                
            df.insert(
                loc=2,
                column='Cedant Name',
                value=df['COMP'].map(cedant_name_dict)
            )
            
            return df
        
        def insert_laspe_factor(self, dataframe):
            """Insert Lapse column with Factor
            """
            
            dataframe['Lapse'] = self.reporting_date - dataframe['Pd End']
            dataframe.loc[
                dataframe['Pd End'] > self.reporting_date,
                'Lapse'] = pd.to_timedelta(0)
            
            dataframe.Lapse = dataframe.Lapse / np.timedelta64(1, 'M')

            dataframe = dataframe.round({'Lapse': 0})

            return dataframe
        
        def get_run_off_rates(self, dataframe):
            """Map run-off rates using Lapse column (in months)
            and UPR column
            """
            df = dataframe.copy()

            path = get_path('run-off')
            run_off_df = pd.read_csv(path, sep='\t')

            df['Run-off'] = df.apply(
                lambda x: run_off_df.loc[
                    x['Lapse'],
                    x['UPR']],
                axis=1
            )
            
            return df
            
        
        def insert_epi_col(self, dataframe):
            """Inserts EPI column with it's proper calculation
            """
            
            df = dataframe.copy()
            # (EPI * (Pd End - Pd Beg + 1) / 365) * Run-off
            df['EPI'] = (
                df['EPI is Rev EPI or EPI'] * (
                    (df['Pd End'] - df['Pd Beg']) / np.timedelta64(1, 'D') + 1
                ) / 365) * df['Run-off']

            df.drop('EPI is Rev EPI or EPI', axis=1, inplace=True)

            return df
        
        def get_grouped_by_contract(self):
            df = self.group_by_contract()
            df_with_names = self.insert_cedant_name(
                df,
                self.create_cedant_dict()
            )
            df_with_lapse_factor = self.insert_laspe_factor(df_with_names)
            df_with_run_off = self.get_run_off_rates(df_with_lapse_factor)
            df_with_epi = self.insert_epi_col(df_with_run_off)

            return df_with_epi

    
    class groupByCedant:
        def __init__(self, dataframe):
            self.dataframe = dataframe

        def get_grouped_by_cedant(self):
            df = self.dataframe
            
            # Helper column for calculating Cedant PD
            df['Step_1_Cedant_PD'] = df['CREDIT_LIMIT_NET_EXPOSURE'] * df['PD']
            
            df_grouped_by_cedant = df.groupby(by='Cedant Name').sum()
            df_grouped_by_cedant['Cedant_PD'] = (
                df_grouped_by_cedant['Step_1_Cedant_PD'] 
                / df_grouped_by_cedant['CREDIT_LIMIT_NET_EXPOSURE']
            )
            
            # Drop helper column
            df_grouped_by_cedant.drop(
                ['PD', 'Step_1_Cedant_PD'],
                axis=1,
                inplace=True
            )

            df_grouped_by_cedant = df_grouped_by_cedant.sort_values(
                by='EC_CONSUMPTION_ND', 
                ascending=False
            )
            
            return df_grouped_by_cedant.reset_index()
        
        def get_final_table_by_cedant(self):
            df = self.get_grouped_by_cedant()

            df.rename(
                columns={
                    'CREDIT_LIMIT_NET_EXPOSURE': 'TPE/100',
                    'EPI': 'EPI (€m)',
                    'EC_CONSUMPTION_ND': 'Ecap (€m)',
                    'EXPECTED_LOSS': 'EL (€m)',
                    'Cedant_PD': 'PD',
                },
                inplace=True
            )

            df = df[[
                'Cedant Name',
                'TPE/100',
                'EPI (€m)',
                'Ecap (€m)',
                'EL (€m)',
                'PD'
            ]]

            df['ECap / TPE'] = df['Ecap (€m)'] / df['TPE/100']
            df['EL / TPE'] = df['EL (€m)'] / df['TPE/100']

            df['ECap / EPI'] = df['Ecap (€m)'] / df['EPI (€m)']
            df['EL / EPI'] = df['EL (€m)'] / df['EPI (€m)']

            # Divide TPE by 100. Not sure why
            df['TPE/100'] = df['TPE/100'] / 100

            return df


class quarterOverQuarter:

    cols_to_drop = [
        'CONTRACT_ID New',
        'CONTRACT_ID Old',
        'CUSTOMER_ID New',
        'CUSTOMER_ID Old',
        'ULTIMATE_ID New',
        'ULTIMATE_ID Old',
        'ULTIMATE_ISO_COUNTRY New',
        'ULTIMATE_ISO_COUNTRY Old',
        'EXPECTED_LOSS New',
        'EXPECTED_LOSS Old',
        'MODEL_SUB_TYPE New',
        'MODEL_SUB_TYPE Old',
    ]
    
    cols_to_rename = {
        'ULTIMATE_NAME New': 'Parent Name',
        'ULTIMATE_RATING_TYPE New': 'New Rating Type',
        'ULTIMATE_RATING_TYPE Old': 'Old Rating Type',
        'ULTIMATE_RATING New': 'New Rating',
        'ULTIMATE_RATING Old': 'Old Rating',
        'CREDIT_LIMIT_NET_EXPOSURE New': 'New Exp',
        'CREDIT_LIMIT_NET_EXPOSURE Old': 'Old Exp',
        'ULTIMATE_POD New': 'New PD',
        'ULTIMATE_POD Old': 'Old PD',
        'EC_CONSUMPTION_ND New': 'New ECap',
        'EC_CONSUMPTION_ND Old': 'Old ECap',
    }

    col_order = [
        'ALIAS_ID',
        'Parent Name',
        'Old PD',
        'New PD',
        '∆ PD',
        'Old Exp',
        'New Exp',
        '∆ Exp',
        'Old ECap',
        'New ECap',
        '∆ ECap',
        'Old Rating Type',
        'Old Rating',
        'New Rating Type',
        'New Rating'
    ]

    index = [
        'TPE',
        'Known Exp',
        'Unknown Exp',
        'EPI',
        'ECap',
        'Unknown ECap',
        'PD',
        'Unknown PD',
        'ECap/TPE',
        'Number of buyers',
        'Known Exp %',
        'Known PD',
        'Known ECap intensity',
        'Unknown ECap intensity',
    ]


    def __init__(
        self,
        product_type,
        this_quarter_reporting_date,
        this_quarter_reporting,
        last_quarter_reporting
    ):
        self.product_type = product_type
        self.this_quarter_reporting_date = this_quarter_reporting_date
        self.this_quarter_reporting = this_quarter_reporting
        self.last_quarter_reporting = last_quarter_reporting
    
    def period_to_string(self, period):
        """
        Retuns New and Old Reporting date, as string

        Parameters
        ----------
        reporting_date (str) : {dd/mm/yyyy}
        period (str) : {'current, 'previous'}
        """
        date = pd.to_datetime(self.this_quarter_reporting_date, dayfirst=True)
        if period == 'current':
            this_quarter = str(date.year)[2:] + 'Q' + str(date.quarter)
            return this_quarter
        elif period == 'previous':
            last_quarter = "{}Q{}".format(
                str((date + relativedelta(months=-3)).year)[2:],
                str((date + relativedelta(months=-3)).quarter)
            )
        
            return last_quarter
        
    def ecap_movement(self):
        
        # ECap being calculated from raw reporting
        df_old = self.last_quarter_reporting

        # Insert Cedant Name to groupby later
        df_old_with_cedant_id = SOReporting.groupByContract.insert_cedant_name(
            dataframe=df_old,
            cedant_name_dict=SOReporting.groupByContract.create_cedant_dict()
        )

        if self.product_type == 'credit':
            df_old_with_cedant_id = df_old_with_cedant_id.loc[
                df_old_with_cedant_id['MODEL_SUB_TYPE'].isin([
                    'CI_COM_KN',
                    'CI_COM_UNK',
                    'CI_POL_KN',
                    'CI_POL_UNK'
                ])
            ]
        elif self.product_type == 'bond':
            raise NotImplementedError

        df_old_with_cedant_id = df_old_with_cedant_id[[
            'Cedant Name',
            'EC_CONSUMPTION_ND'
        ]]

        df_old_with_cedant_id = df_old_with_cedant_id.groupby(
            by='Cedant Name'
        ).sum().reset_index()
        
        # ECap being calculated from raw reporting
        df_new = self.this_quarter_reporting

        # Insert Cedant Name to groupby later
        df_new_with_cedant_id = SOReporting.groupByContract.insert_cedant_name(
            dataframe=df_new,
            cedant_name_dict=SOReporting.groupByContract.create_cedant_dict()
        )

        if self.product_type == 'credit':
            df_new_with_cedant_id = df_new_with_cedant_id.loc[
                df_new_with_cedant_id['MODEL_SUB_TYPE'].isin([
                    'CI_COM_KN',
                    'CI_COM_UNK',
                    'CI_POL_KN',
                    'CI_POL_UNK'
                ])
            ]
        elif self.product_type == 'bond':
            raise NotImplementedError
        
        df_new_with_cedant_id = df_new_with_cedant_id[[
            'Cedant Name',
            'EC_CONSUMPTION_ND'
        ]]

        df_new_with_cedant_id = df_new_with_cedant_id.groupby(
            by='Cedant Name'
        ).sum().reset_index()

        df = df_old_with_cedant_id.merge(
            df_new_with_cedant_id,
            how='outer',
            on='Cedant Name',
            suffixes=(" " + self.period_to_string('previous'),
                      " " + self.period_to_string('current'))
        )

        # 2020Q1 Clal had Zero ECap, so it was showing as NaN
        df.fillna(0, inplace=True)

        # To keep it simple, I'm using column index. 
        # Last quarter and this quarter will always remain 
        # at index 1 and 2
        df['Δ'] = df.iloc[:, 2] - df.iloc[:, 1]

        df.sort_values(by='Δ', ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        return df

    def filter_df(self, dataframe, balloon_id):
        """Exclude from Pandas political risk unknown 
        and leaves only Specific Balloon ID
        
        Parameters
        ----------
        dataframe: Pandas.DataFrame
            dataframe to be filtered
        """

        df = dataframe.copy()

        df = df.loc[df['CUSTOMER_ID'] == balloon_id]

        if self.product_type == 'credit':
            # Set TPE to 0 to be able to groupby ALIAS_ID
            df.loc[
                df['MODEL_SUB_TYPE'].isin(['CI_POL_KN', 'CI_POL_UNK']),
                'CREDIT_LIMIT_NET_EXPOSURE'
            ] = 0

            # Set PD to 0 to be able to groupby ALIAS_ID
            df.loc[
                df['MODEL_SUB_TYPE'].isin(['CI_POL_KN', 'CI_POL_UNK']),
                'ULTIMATE_POD'
            ] = 0

            df = df.groupby(by='ALIAS_ID').sum().reset_index()

            # Groupby loses all str fields. Now we have to bring it back
            # Filter out all POL ALIAS_ID's to avoid duplicates
            df_info = dataframe.copy()
            df_info = df_info.loc[
                (df_info['CUSTOMER_ID'] == balloon_id)
                & (~df_info['MODEL_SUB_TYPE'].isin(
                    ['CI_POL_UNK', 'CI_POL_KN']
                ))
            ]

            df_info = df_info[[
                'ALIAS_ID',
                'ULTIMATE_ID',
                'CUSTOMER_ID',
                'CONTRACT_ID',
                'ULTIMATE_NAME',
                'ULTIMATE_RATING_TYPE',
                'ULTIMATE_RATING',
                'MODEL_SUB_TYPE',
                'ULTIMATE_ISO_COUNTRY',

            ]]

            df = df.merge(df_info, on='ALIAS_ID')
        
        elif self.product_type == 'bond':
            political = df['MODEL_SUB_TYPE'].str.contains('CI_POL_UNK')
            df = df.loc[~political]
        
        return df
    
    def format_merged_deep_dive(self, dataframe):
        
        df = dataframe
        cols_to_rename = quarterOverQuarter.cols_to_rename.copy()
        col_order = quarterOverQuarter.col_order.copy()

        df.drop(quarterOverQuarter.cols_to_drop, axis=1, inplace=True)

        # To Make sure risks from both quarters have an Ultimate Name
        condition = df['ULTIMATE_NAME New'].isna()
        df.loc[condition, 'ULTIMATE_NAME New'] = df['ULTIMATE_NAME Old']
        
        # We only need 1 name column
        df.drop('ULTIMATE_NAME Old', axis=1, inplace=True)

        

        if self.product_type == 'credit':
            cols_to_rename['RSQUARED New'] = 'New RSquared'
            cols_to_rename['RSQUARED Old'] = 'Old RSquared'

            col_order.extend([
                'New RSquared',
                'Old RSquared'
            ])
        
        df.rename(columns=cols_to_rename, inplace=True)

        # Just initialize the columns with value Zero to avoid pandas.insert
        # errors
        df['∆ PD'] = 0
        df['∆ Exp'] = 0
        df['∆ ECap'] = 0

        return df[col_order]
    
    @staticmethod
    def insert_calculation_cols(dataframe):
        """Inserts Delta columns into Deep Dive Dataframe
        """
        df = dataframe.copy()

        # This is to avoid calculation error when Cedants don't have Rating
        
        cols_fill_na = [
            'New PD',
            'Old PD',
            'New Exp',
            'Old Exp',
            'Old ECap',
            'New ECap'
        ]

        for col in cols_fill_na:
            df.loc[df[col].isna(), col] = 0

        df['∆ PD'] = df['New PD'] - df['Old PD']
        df['∆ Exp'] = df['New Exp'] - df['Old Exp']
        df['∆ ECap'] = df['New ECap'] - df['Old ECap']

        return df
    
    def get_deep_dive_exposures(self, balloon_id):
        print('Cedant treaty type is: {}'.format(self.product_type))

        df_new = self.filter_df(self.this_quarter_reporting, balloon_id)
        df_old = self.filter_df(self.last_quarter_reporting, balloon_id)

        df_merged = df_new.merge(
            df_old,
            how='outer',
            on='ALIAS_ID',
            suffixes=(' New', ' Old')
        )

        df_formatted = self.format_merged_deep_dive(df_merged)
        df_with_deltas = self.insert_calculation_cols(df_formatted)

        # This is just to clearly state that it's unknown exposure
        df_with_deltas.loc[
            df_with_deltas['ALIAS_ID'] == balloon_id,
            'Parent Name'
        ] = 'Unknown Exposure'

        return df_with_deltas.sort_values(by='New ECap', ascending=False)
    
    def create_deep_dive_summary_df(self):
        """Creates empty DataFrame with the main
        Indexes and Columns
        """

        this_quarter = self.period_to_string('current')
        last_quarter = self.period_to_string('previous')
        cols = [last_quarter, this_quarter]

        df = pd.DataFrame(index=quarterOverQuarter.index, columns=cols)
        return df
    
    def get_deep_dive_summary(
        self,
        balloon_id,
        this_quarter_grouped_by_contract,
        last_quarter_grouped_by_contract
    ):
        df = self.create_deep_dive_summary_df()
        cedant_df = self.get_deep_dive_exposures(balloon_id=balloon_id)
        
        this_quarter = self.period_to_string('current')
        last_quarter = self.period_to_string('previous')

        indexes = ['Exp', 'ECap', 'PD']

        period = [last_quarter, this_quarter]
        string = ['Old', 'New']

        # To filter only unknown exposure
        only_unk = cedant_df['ALIAS_ID'] == balloon_id
        for index in indexes:
            for i in range(2):
                col = string[i] + ' ' + index
                df.loc['Unknown ' + index, period[i]] = cedant_df.loc[
                    only_unk,
                    col
                ].sum()
            
        
        df.loc['TPE', last_quarter] = cedant_df['Old Exp'].sum()
        df.loc['TPE', this_quarter] = cedant_df['New Exp'].sum()

        df.loc['Known Exp', last_quarter] = (
            df.loc['TPE', last_quarter]
            - df.loc['Unknown Exp', last_quarter]
        )

        df.loc['Known Exp', this_quarter] = (
            df.loc['TPE', this_quarter]
            - df.loc['Unknown Exp', this_quarter]
        )

        df.loc['EPI', this_quarter] = this_quarter_grouped_by_contract.loc[
            this_quarter_grouped_by_contract['Balloon ID'] == balloon_id,
            'EPI'
        ].sum()

        df.loc['EPI', last_quarter] = last_quarter_grouped_by_contract.loc[
            last_quarter_grouped_by_contract['Balloon ID'] == balloon_id,
            'EPI'
        ].sum()
        
        df.loc['ECap', last_quarter] = cedant_df['Old ECap'].sum()
        df.loc['ECap', this_quarter] = cedant_df['New ECap'].sum()

        for i in range(2):
            df.loc['PD', period[i]] = (
            (cedant_df['{} PD'.format(string[i])] 
            * cedant_df['{} Exp'.format(string[i])]).sum()
            / cedant_df['{} Exp'.format(string[i])].sum()
        )

        for quarter in period:
            df.loc['ECap/TPE', quarter] = (
                df.loc['ECap', quarter]
                / df.loc['TPE', quarter]
            )
        
        for i in range(2):
            df.loc['Number of buyers', period[i]] = cedant_df.loc[
                cedant_df['{} PD'.format(string[i])] > 0,
                '{} PD'.format(string[i])
            ].value_counts().sum()

        for quarter in period:
            df.loc['Known Exp %', quarter] = (
                df.loc['Known Exp', quarter]
                / df.loc['TPE', quarter]
            )

        for i in range(2):
            df.loc['Known PD', period[i]] = (
                (cedant_df.loc[~only_unk, '{} PD'.format(string[i])]
                * cedant_df.loc[~only_unk, '{} Exp'.format(string[i])]).sum()
                / cedant_df.loc[~only_unk, '{} Exp'.format(string[i])].sum()
            )
        
        
        for quarter in period:
            df.loc['Known ECap intensity', quarter] = (
                (df.loc['ECap', quarter]
                - df.loc['Unknown ECap', quarter])
                / df.loc['Known Exp', quarter]
            )
        
        for quarter in period:
            df.loc['Unknown ECap intensity', quarter] = (
                df.loc['Unknown ECap', quarter]
                / df.loc['Unknown Exp', quarter]
            )
        
        return df