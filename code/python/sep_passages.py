import pandas as pd
'''
Dump every set of chunks per topic into its own file
'''
df_pass = pd.read_csv('/newdata/covid10k/outputs/passages_2019.csv')

for topic in range(50):
    df_topic = df_pass[df_pass['Topic'] == topic]
    df_topic = df_topic[['Filename','Text']]
    df_topic.to_csv(f'../../outputs/2019_topic_chunks/topic_{topic}_passages.csv')