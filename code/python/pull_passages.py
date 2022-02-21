import pandas

# Get job text
report_text = pandas.read_csv("/newdata/covid10k/outputs/test2_2019.txt", sep="\t", header=None, low_memory=False)
report_text.columns = ["Identifier", "Filename", "Text"]

# Column 0 in doctopics is an incrementing integer, drop it
# The new column 0 is the identifier and columns 1-101 are the topic proportions 

doctopics = pandas.read_csv("/newdata/covid10k/outputs/test_2019.doctopics.txt", sep="\t", header=None)
doctopics = doctopics.drop(0, axis=1)
doctopics.columns = range(0, 51)

# Merge job text and topic proportions
doctopics = doctopics.merge(report_text, left_on=0, right_on="Identifier")
df_final = pandas.DataFrame(columns=["Identifier", "Filename", "Text", "Topic",])


for i in range(50):
    # Grab the top 10 ids by a given topic's proportion
    top_id = doctopics.sort_values(i, ascending=False).drop_duplicates("Filename")[0][:10]
    filtered = doctopics[doctopics[0].isin(top_id)][[0, "Filename", "Text"]]
    filtered['Topic'] = i
    filtered.columns = ["Identifier", "Filename", "Text", "Topic"]
    df_final = pandas.concat([df_final,filtered], axis=0)
df_final.to_csv('../../outputs/passages_2019.csv')
#filtered.to_csv('../../outputs/passages.csv')



'''
writer = pandas.ExcelWriter('top_chunks.xlsx', engine='xlsxwriter')

for i in range(1, 51):
    # Grab the top 10 ids by a given topic's proportion
    top_id = doctopics.sort_values(i, ascending=False).drop_duplicates("Filename")[0][:10]
    filtered = doctopics[doctopics[0].isin(top_id)][[0, "Filename", "Text"]]
    filtered.columns = ["Identifier", "Filename", "Text"]
    filtered.to_excel(writer, index=False, sheet_name=str(i - 1))
writer.save()
'''