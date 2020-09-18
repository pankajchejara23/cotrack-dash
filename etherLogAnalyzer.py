"""
This library process the etherpad logs.
Author: Pankaj
Date: 9/09/2019

"""

# import package
import pandas as pd
import datetime



class etherLogAnalyzer(object):
    """
    init function initialize the etherLogAnalyzer object.
    it takes one parameter the file name as
    """
    def __init__(self, file_name):
        self.file_name = file_name

        try:
            self.file = pd.read_csv(file_name,names=['timestamp','ip','action','oldlen','newlen','changeset','charbank','noadd','noremove'])
            print('File loaded successfully....')

            self.file['timestamp'] = pd.to_datetime(self.file['timestamp'])
            #print('Setting timestamp as index...')
            self.file = self.file.set_index(pd.DatetimeIndex(self.file['timestamp']))

        except Exception as e:
            print('Error occured while opening the file',str(e))

    def getDuration(self):
        #self.file['timestamp'] = pd.to_datetime(self.file['timestamp'],format="%Y-%m-%d %I:%M:%S")
        self.file['timestamp'] = pd.to_datetime(self.file['timestamp'])
        df1=self.file
        return str(df1.timestamp[df1.shape[0]-1]-df1.timestamp[0])


    # return all the text generated in Etherpad

    def getAllText(self):
        return self.file.charbank.tolist()

    """
    This function will return the number of total ip recorded in the log file.
    """

    def getAuthorCount(self):
        return len(self.file.ip.unique())

    """
    This function returns the list of Author's IP recorded in the log file.
    """

    def getAuthorIP(self):
        return self.file.ip.unique()

    """
    Logs are recorded in same file for all the pads, therefore this function will seperate the log file
    on the basis of group. It reuires parameter e.g. group name and group ips.
    @params: group_name (String): name of group
             group_ips (List): list containing ips belong to that group
    Return type: Pandas dataframe.
    """

    def getLogForGroup(self,group_ips):
        temp_df = self.file[self.file.ip.isin(group_ips)]
        return temp_df

    """
    This function will generate statistics for each author in the group. These statistics are in form of number of addition
    and deletion along with time.
    @params:
       ip (String): ip address for which you want to see the stats
       timescale (String): it specify the time window for aggregating statistics.
       Possible values: Alias   Description
                        B       business day frequency
                        C       custom business day frequency (experimental)
                        D       calendar day frequency
                        W       weekly frequency
                        M       month end frequency
                        BM      business month end frequency
                        CBM     custom business month end frequency
                        MS      month start frequency
                        BMS     business month start frequency
                        CBMS    custom business month start frequency
                        Q       quarter end frequency
                        BQ      business quarter endfrequency
                        QS      quarter start frequency
                        BQS     business quarter start frequency
                        A       year end frequency
                        BA      business year end frequency
                        AS      year start frequency
                        BAS     business year start frequency
                        BH      business hour frequency
                        H       hourly frequency
                        T, min  minutely frequency
                        S       secondly frequency
                        L, ms   milliseonds
                        U, us   microseconds
                        N       nanoseconds
        plot(Boolean): Specify True if you want to plot the graph


     Return type: Dataframe


    """

    def generateWindowWiseStats(self,window_size='30S',ips=[]):

        # Computer number of char added or deleted
        #print("IP",ips)
        tempdf = self.file.copy()
        #print(tempdf.shape)
        temp = tempdf.loc[tempdf['ip'].isin(ips)]
        temp['addition'] = temp['newlen']-temp['oldlen']
        temp['deletion'] = temp['oldlen']-temp['newlen']
        mask = temp['addition']<0
        mask2 = temp['deletion']<0
        temp.loc[mask,'addition']=0
        temp.loc[mask2,'deletion']=0



        #self.file['timestamp'] = pd.to_datetime(self.file['timestamp'],format="%Y-%m-%d %I:%M:%S")



        df1=temp.copy()

        # Computing timedelta
        time_delta = pd.to_timedelta(window_size)

        # Creating empty dataframe
        final = pd.DataFrame(columns=['timestamp','u1_add','u1_del','u1_text','u2_add','u2_del','u2_text','u3_add','u3_del','u3_text','u4_add','u4_del','u4_text'])

        if df1.shape[0] != 0:
            cur_ts = df1.timestamp[0]
        else:
            print("Empty frame")
            return final


        while cur_ts < df1.timestamp[df1.shape[0]-1]:

            next_ts = cur_ts + time_delta

            temp_log_df = df1.between_time(datetime.datetime.time(cur_ts),datetime.datetime.time(next_ts),include_start=True,include_end=False)


            entry = self.extractFeatures(cur_ts,temp_log_df,ips)

            #final = final.append({'timestamp':entry['timestamp'],'u1_add':entry['u1_add'],'u1_del':entry['u1_del'],'u1_text':entry['u1_text'],'u2_add':entry['u2_add'],'u2_del':entry['u2_del'],'u2_text':entry['u2_text'],'u3_add':entry['u3_add'],'u3_del':entry['u3_del'],'u3_text':entry['u3_text'],'u4_add':entry['u4_add'],'u4_del':entry['u4_del'],'u4_text':entry['u4_text'],'u1_speak':entry['u1_speak'],'u2_speak':entry['u2_speak'],'u3_speak':entry['u3_speak'],'u4_speak':entry['u4_speak'],'speak_sequence':entry['speak_sequence']},ignore_index=True)
            final = final.append(entry,ignore_index=True)

            cur_ts = next_ts
        final.to_csv('Final.csv',index=False)
        return final


    def extractFeatures(self,timestamp,log_df, no_ip):
        # features
        user1_addition = 0
        user1_deletion = 0
        user1_text = ""

        user2_addition = 0
        user2_deletion = 0
        user2_text = ""

        user3_addition = 0
        user3_deletion = 0
        user3_text = ""

        user4_addition = 0
        user4_deletion = 0
        user4_text = ""


        def concatenate_list_data(list):

            result= ''
            for element in list:
                if str(element) != 'nan':
                    result += str(element)
            return result


        u1 = log_df.loc[log_df['ip']==no_ip[0],:]
        u2 = log_df.loc[log_df['ip']==no_ip[1],:]
        u3 = log_df.loc[log_df['ip']==no_ip[2],:]
        u4 = log_df.loc[log_df['ip']==no_ip[3],:]


        user1_addition = u1.addition.sum()
        user1_deletion = u1.deletion.sum()
        user1_text = concatenate_list_data(u1.charbank.tolist())

        user2_addition = u2.addition.sum()
        user2_deletion = u2.deletion.sum()
        user2_text = concatenate_list_data(u2.charbank.tolist())

        user3_addition = u3.addition.sum()
        user3_deletion = u3.deletion.sum()
        user3_text = concatenate_list_data(u3.charbank.tolist())

        user4_addition = u4.addition.sum()
        user4_deletion = u4.deletion.sum()
        user4_text = concatenate_list_data(u4.charbank.tolist())




        return {'timestamp':timestamp,'u1_add':user1_addition,'u1_del':user1_deletion,'u1_text':user1_text,'u2_add':user2_addition,'u2_del':user2_deletion,'u2_text':user2_text,'u3_add':user3_addition,'u3_del':user3_deletion,'u3_text':user3_text,'u4_add':user4_addition,'u4_del':user4_deletion,'u4_text':user4_text}




    def generateStatsForAuthor(self,ip,plot=False,timescale='30S'):
        temp = self.file.copy()
        temp = temp.loc[temp['ip']==ip,:]
        temp['addition'] = temp['newlen']-temp['oldlen']
        temp['deletion'] = temp['oldlen']-temp['newlen']
        mask = temp['addition']<0
        mask2 = temp['deletion']<0
        temp.loc[mask,'addition']=0
        temp.loc[mask2,'deletion']=0
        stat = temp.groupby(pd.Grouper(freq=timescale)).sum()
        if plot:
            stat[['addition','deletion']].plot(kind='bar')
            plt.title('Stats for User:'+ip)
        return stat
