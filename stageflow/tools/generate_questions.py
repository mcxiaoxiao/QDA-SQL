from tools.db_detail import bird_getdesc
from tools.sql_execute import sqlite_execute as execute
import random

#sql执行工具
def bird_sql_evoke(query,db_name):
    result, execution_time ,executable = execute("datasets/cosql_dataset/database/"+db_name+"/"+db_name+".sqlite",query)
    return result 

def get_example(db_name):
    sql_query = "SELECT name FROM sqlite_master WHERE type='table';"
    result = bird_sql_evoke(sql_query,db_name)

    #组织每个table的数据案例
    column_example=""
    for table_name in result:
        column_example = column_example + table_name[0] + ":\n"
        sql_get_eg = "SELECT * FROM "+ table_name[0] +" LIMIT 3;"
        table_eg = bird_sql_evoke(sql_get_eg,db_name)
        for table_data in table_eg:
            column_example = column_example + '('
            for column_data in table_data: 
                column_example = column_example + str(column_data) +','
            column_example = column_example[:-1] + ')\n'
    return column_example
# ——————————————————
# 无分类情况
# 下的各种prompt:
# ——————————————————

def get_utterance(goal_sql,utterances_before,last_sql,db_name,warning=""): 
    #获取描述
    description = bird_getdesc(db_name)
    
    column_example = get_example(db_name)

    question = "最终SQL:" + goal_sql + "\n先前用户问题:" + utterances_before + "\n上一个SQL回答:" + last_sql + "\n数据库描述:" + description + "\n各table数据示例:"+ column_example + "\n"+"你作为问问题的用户，根据以上信息，你需要提出一个问题，确保根据你提出的问题结合先前问题可以产生可执行SQL(比如以以下4种方式结合 1、Refinement，即当前问题和上一个问题问的还是同一个实体，但约束条件不一样了。  - 前一个问题是：哪个专业的学生最少？  - 后一个问题是：哪个专业最受欢迎？（即哪个专业学生最多？）。  - 问的都是【专业】这个实体，只是约束条件变化了。2、Theme-entity，即当前问题问的是上一个问题中提到实体的其他属性。- 前一个问题是：Anonymous Donor Hall 这个大厅的容量是多少？- 后一个问题是：列出它的所有便利设施。（即 Anonymous Donor Hall 大厅的所有便利设施有哪些？）。 - 问的都是关于【Anonymous Donor Hall】这个实体，只是两个问题所问的实体属性不同。- 3、Theme-property，即当前问题问的是另外一个实体的同一个属性。 - 前一个问题是：告诉我 Double Down 这集的【排名】是多少。 - 后一个问题是：那么 Keepers 这集呢？（即 Keepers 这集的【排名】是多少？）。 - 问的都是【排名】这个属性，只是对应的实体不一样。- 4、Answer refinement，即当前问题问的是上一个问题的子集。 - 前一个问题是：请列出【所有系】的名字？ - 后一个问题：【统计系】所有老师的平均薪资是多少？ - 很显然，【所有系】→ 【统计系】)，你提出的问题可以参考但不同于最终SQL的问题，（如果包含主语则你的问题的主语是我）只用人类口吻给我问题不要除了问题本身以外的任何其余内容,问题要做到最简化"+warning
    
    return question


def get_sql(utterances_before,utterance_now,db_name): 
    #获取描述
    description = bird_getdesc(db_name)
    
    question = "先前用户问题:"+utterances_before+"\n当前用户问题:"+utterance_now+"\n数据库描述:"+description+"\n参照先前用户问题结合当前用户问题写一个SQL回答当前问题（不带任何解释的只给我SQL代码本体）"
    
    return question 

def get_summary(utterances,final_sql,db_name):
    #获取描述
    description = bird_getdesc(db_name)
    
    question = "根据先前问句:"+utterances+"\n以及数据库描述:"+description+"\n为我总结出可以用sql:"+final_sql+"回答的总结性问题，只用人类口吻给我问题，不要除了问题以外的任何其余内容。"
    
    return question 

# ——————————————————
# 有分类情况
# 下的各种prompt:
# ——————————————————

classes = "You are the questioner responsible for asking questions based on the database information. You will refer to the database description and table data examples of the database to ask questions and serve as system. The question type can be the following dialogue behaviors:INFORM_SQL: Users provide requests through SQL. If the user's question can be answered through SQL, the system needs to write SQL and description such as 'These are the xxx of'/'This is' INFER_SQL: If the user's question must be answered through SQL and human inference. For example, if the user's question is a yes/no question, or about 'the third oldest...', SQL cannot return the answer directly (or is too complex), but we can infer the answer based on the SQL results.AMBIGUOUS: The user's question is ambiguous and the system needs to reconfirm the user's intent (e.g., 'Did you mean...?') or ask the user to specify which columns or values to return.AFFIRM: Confirm what the system said (the user agrees/affirms).NEGATE: Negate what the system said (the user disagrees/denies it such as 'no,i mean ...').CANNOT_ANSWER: The question contains additional information not found in the database. (When the user is unfamiliar with the database schema or its implications or colums)The system cannot easily answer the user's question via SQL, and the system informs the user of its limitations.The system needs to detect what information the user needs but is not included in the database. IMPROPER: include(GREETING GOODBYE THANK_YOU)Inappropriate questions, such as small talk('hello','hey',''good morning') or questions asking for advice The system should answer smooth and reasonable daily answersFor the system. define the following dialog behavior:CONFIRM_SQL: The system creates a natural language response describing the SQL and results table, and asks the user to confirm that the system understood his/her intent.CLARIFY: Asks the user to reconfirm and clarify his/her intentions when their question is ambiguous.REJECT: Tells the user that the system did not understand/cannot answer his/her question, or that the user's question is irrelevant to the topic.REQUEST_MORE: Ask the user if they need more information.GREETING: Greeting the user.SORRY: Apologize to the user.WELCOME: Tell users you are welcome! .GOOD_BYE: Politely say goodbye to the user.\n"

def get_infer(db_name,utterance,goal_sql):
    description = bird_getdesc(db_name)
    column_example = get_example(db_name)
    question = ''+classes+'Database description:\n'+description+'Data example:\n'+column_example+"Refer to goal_sql below.The generated sqls can be different from goal_sql:"+goal_sql+"generate 2 user dialogue（behavior type: INFER_SQL）in json format without explanation[{text:"",sql:""},{text:"",sql:""},{text:"",sql:""}.....]"+utterance
    return question

def get_infer_des(text,sql_query,db_name):
    result = bird_sql_evoke(sql_query,db_name)
    question = 'the question is:"'+text+'"the SQL query is:"'+sql_query+'" the output of the sql is:"'+str(result)+'"based on the question SQL and output generate a description to answer the question in json format{description:""}'
    return question
    
def get_confirm(db_name,utterance,goal_sql):
    description = bird_getdesc(db_name)
    column_example = get_example(db_name)
    question = ''+classes+'Database description:\n'+description+'Data example:\n'+column_example+"Refer to goal_sql below.The generated sqls can be different from goal_sql:"+goal_sql+"generate 2 user dialogue（behavior type: INFORM_SQL）in json format without explanation[{text:"",sql:"",description:""},{text:"",sql:"",description:""},{text:"",sql:"",description:""}.....]"+utterance
    return question

def get_cannot(db_name,utterance,goal_sql):
    description = bird_getdesc(db_name)
    column_example = get_example(db_name)
    
    Category = {
        'Column Unanswerable':"\nQuestion: Show me model name by sales. \nColumns: BrandName, Sales, Year \nNote: The span “model name” is unanswerable because no such a column refers to this.",
        'Calculation Unanswerable':"\nQuestion Example: What is the balance of trade of China?\nColumns: Country, Imports, Exports, ... \nNote: The span “balance of trade” is unanswerable, because Input does not include this  evidence of the calculation formula : Balance of Trade = Exports – Imports."
    }
    
    catname, catdesc = random.choice(list(Category.items()))
    
    question = ''+classes+'Database description:\n'+description+'Data example(Only a tiny fraction of the data in the database):\n'+column_example+"Refer to goal_sql below and database\'s description.The generated sqls can be different from goal_sql"+goal_sql+"generate 1 user-system dialogue（behavior type: CANNOT_ANSWER Simply and clearly apologise and tell the user the explanation of reason why the user issue is not buildable for the sql such as which colums are not in this database）output only in json format{user:"",explanation:""}Detailed requirements of the QA:"+catname+" Example:"+catdesc+utterance+"Ask a clearly unanswerable question based on the database and explain why."
    return question
    
def get_improper(db_name,utterance,goal_sql):
    description = bird_getdesc(db_name)
    column_example = get_example(db_name)

    
    question = ''+classes+'Database description:\n'+description+'Data example:\n'+column_example+utterance+"\nbase on previous question generate a IMPROPER question（if dont have previous question you can not output GOOD_BYE/WELCOME/THANK_YOU,just talk somthing else）.generate a user-system dialogue based on the database i provide(if the question not related to the database,answer it in your way!)（behavior type: GOOD_BYE/THANK_YOU/WELCOME(chose one randomly)in json format[{question:'',question_type:'',answer:'',answer_type:REQUEST_MORE/GREETING/SORRY/WELCOME/GOOD_BYE(chose one of them)}]Don't output anything other than json"
    return question

def get_ambiguous(db_name,utterance,goal_sql):
    options = ["INFER_SQL (include NEGATE)", "INFER_SQL", "INFORM_SQL (include NEGATE)", "INFORM_SQL"]
    choice1 = random.choice(options)
    # print('random chose :'+choice1)
    # 使用 split() 函数分隔字符串
    split_choice1 = choice1.split()
    # 取第一个元素（索引为0）
    first_element1 = split_choice1[0]
    description = bird_getdesc(db_name)
    column_example = get_example(db_name)
    
    Category = {
        'Column Ambiguity':"\nQuestion:Show me the top rating movie. \nColumns: Movie, IMDB Rating, Rotten Tomatoes Rating, Content Rating \nNote: The token 'rating' in question is ambiguous because there are 3 column names containing 'rating'. The users question is ambiguous, the system needs to double check the user’s intent (e.g. what/did you mean by...?) or ask for which columns to return.",
        'Subjective Ambiguity':"\nQuestion: Is this movie any good?\nNote: conditions of operators (ambiguity in values), such as finding the “good” movie while “good” is an ambiguous measurement for selecting a correct value. The system should indicate the ambiguous part and ask the user to clarify."
    }
    
    catname, catdesc = random.choice(list(Category.items()))
    
    question = ''+classes+'Database description:\n'+description+'Data example:\n'+column_example+utterance+"\nbase on previous question generate a AMBIGUOUS-CLARIFY-"+choice1+"dialogue.Refer to goal_sql below(The generated sqls should be different from the goal_sql):"+goal_sql+'generate a dialogue in json format without explanation[{"ambiguous_question":""(To make sure that the question is indeed impossible to answer directly base on the information  above),"clarify_answer":"","question":""(type:'+choice1+'),"sqlquery":""(Ensure the sql query about the question will definitely output data),"type":"'+first_element1+'"(dont change),"description":""(if type is INFORM_SQL you should give this description)}]'+'Detailed requirements:'+catname+' Example:'+catdesc+utterance
    return question

# ——————————————————
# 筛选步骤
# 下的各种prompt:
# ——————————————————
def critic_cannot(db_name,previous,q,evidence):
    description = bird_getdesc(db_name)
    
    column_example = get_example(db_name)

    question = 'Database description:'+description+'\nTable data example:'+str(column_example)+'\nprevious Q&As:'+str(previous)+'\nquestion:'+str(q)+'\nevidence:'+str(evidence)+'According to the database description,Table data examples previous Q&As and the evidence, can this question be achieved with more complex sql or multi-table join query for valid sql? If it works then {"answerable": "yes"} otherwise {"answerable": "no"}.output with nothing else just json'
    return question


def critic_ambiguous(db_name,qa_pairs,evidence):
    description = bird_getdesc(db_name)
    
    column_example = get_example(db_name)

    question = 'Database description:'+description+'\nTable data example:'+str(column_example)+'\nprevious Q&As:'+str(previous)+'\nquestion:'+str(qa_pairs)+'\nevidence:'+str(evidence)+'According to the database description,Table data examples,previous Q&As and the evidence,based on the informations given to this question can you generate a definitive sql, if the system really needs more information to generate the exact sql then output \'yes\', otherwise modify this Q&A pair to INFORM_SQL-CONFIRM_SQL Q&A pair.output in json format[{"text":"","type":"INFORM_SQL","isuser":"True"(double-quoted)},{"text":"","sqlquery":"","type":"CONFIRM_SQL","isuser":"false"(double-quoted)}]INFORM_SQL: Users provide question can be answered through SQL CONFIRM_SQL: The system creates sql and a natural language response "text" to describe the significance of the results found through sql ,text can\'t refer to sql query results. '
    return question

def critic_refine(db_name,qa_pairs,evidence):
    description = bird_getdesc(db_name)
    
    column_example = get_example(db_name)

    behaviors = '''type of behaviors:
The user question type can be the following dialogue behaviors:
INFORM SQL: Users provide requests through natural language question. If the user's question can be answered through SQL, the system needs to write SQL and explain（dont need to explain based on the SQL results）
INFER SQL: If the user's question must be answered through SQL and human inference. For example, if the user's question is a "yes/no" question, or about "the third oldest...", SQL cannot return the answer directly (or is too complex), but we can infer the answer based on the SQL results.
AMBIGUOUS: The user's question is ambiguous and the system needs to reconfirm the user's intent (e.g., "Did you mean...?") or ask the user to specify which columns or values to return.
AFFIRM: Confirm what the system said (the user agrees/affirms).
NEGATE: Negate what the system said (the user disagrees/denies it).
CANNOT_ANSWER: The question contains additional information not found in the database. (When the user is unfamiliar with the database schema or its implications) The system cannot easily answer the user's question via SQL, and the system informs the user of its limitations.The system needs to detect what information the user needs but is not included in the database.
IMPROPER:Inappropriate questions, such as small talk or questions asking for advice.The system should answer smooth and reasonable daily answers
For the system, define the following dialog behavior:
CONFIRM SQL: The system creates a natural language response describing the SQL and results table, and asks the user to confirm that the system understood his/her intent.
CLARIFY: Asks the user to reconfirm and clarify his/her intentions when their question is ambiguous.
REJECT: Tells the user that the system did not understand/cannot answer his/her question, or that the user's question is irrelevant to the topic.
REQUEST MORE: Ask the user if they need more information.
GREETING: Greeting the user.
SORRY: Apologize to the user.
WELCOME: Tell users you are welcome! .
Only 5 Q&A combinations are allowed Type 1:INFER_SQL-CONFIRM SQL Type 2: AMBIGUOUS-CLARIFY-INFER_SQL/INFORM SQL Type 3:INFORM_SQL-CONFIRM_SQL Type 4:CANNOT_ANSWER-SORRY Type 5: IMPROPER-REQUEST MORE/GREETING/SORRY
/WELCOME/GOOD BYE
    '''
    
    Requirements_b = '''Requirements
1 The user's question and the system's answer match the type of behavior, and the system gives a completely correct and detailed answer that fully satisfies the user's needs.
2 The system's answer is completely relevant to the user's question, with no extraneous or jumping content, and excellent coherence.
3 The system's answers are completely relevant to the user's question, with no irrelevant or off-topic content.
4 The system's answers show a high degree of variability, with a high degree of diversity in language expression and content, and a high degree of innovation and novelty.
5 Domain knowledge must be included in generated Q&As:"'''
    
        
    Requirements_a = '''" .Q&A needs to be replaced by the domain knowledge directly in the Q&As,Use domain knowledge rather than table fields wherever possible.
6 Modify the wrong query according to the database description and result output, if the wrong question belongs to INFER_SQL then change it to INFORM_SQL and modify the Q&A.
7 If there is CANNOT_ANSWER please focus on its question (text) according to the database description is not likely to be able to answer, please determine that this type of question is really not possible to generate sql, you have to modify the Q&A into right type.
8 For AMBIGUOUS types of questions, making the Q&A more ambiguous makes their CLARIFY follow-up questions more meaningful.makes it completely impossible to generate the corresponding sql.
9 If type is incorrectly labeled, please change it. Note: there are only five combinations of type.
isuser:"True" means this is a user question, in the tone of the user's question.
isuser:false means this is a system answer, in the tone of the system answer.
Make the text field sentences of user questions and system responses express a tone that is appropriate to their role
type indicates the type of behavior, if it does not match the description, then modify the Q&A, if the deviation is large, then delete the group of Q&A.
Case-by-case checking for fulfillment of requirements to filter and modify the Q&As, output in json format only[{"isuser":"True","text": "","type": ""},{"isuser":"False","text": "","type": "",(CONFIRM_SQL also need "query" field)"query":""},....]Values in json must be enclosed in double quotes.
    '''
    
    question = "you are SQL professional:"+behaviors+'Database description:'+description+'\nTable data example:'+str(column_example)+'Q&As:'+str(qa_pairs)+Requirements_b+str(evidence)+Requirements_a
    
    return question


def include_knowledge(evidence,db_name,turns):
    # question = 'Q&As:'+str(turns)+'\nDomain knowledge:'+str(evidence)+'Modify the text in the problem using the domain knowledge(Direct replacement without comments)，Modify only what can be modified without changing the meaning of the questions and answers,If something mentioned above appears in the following text, rewrite it so that it omits the part mentioned above, making the whole conversation more natural. And make the tone of the "text" content output by the user and the system authentic and natural.Output the json in its original format with only the text part modified.,Capitalize True and False.'
    
    question = 'Q&As:'+str(turns)+'Modify only what can be modified without changing the meaning of the questions and answers,If the question is not complete then refer to the sql to complete it.Questions need to be completed if they are not complete enough.If something mentioned above appears in the following text, rewrite it so that it omits the part mentioned above.Entities that already appear above should be omitted with pronouns.making the whole conversation more natural. And make the tone of the "text" content output by the user and the system authentic and natural.Output the json in its original format with only the text part modified.,Capitalize True and False.'
    return question

def score_sql(previous,result,question,sql):
    question='Based on previous \nQAs:"'+str(previous)+'\nWhat are the types of data that the system might need to answer the user\'s question:'+str(question)+'"? \nSQL:'+str(sql)+'\noutputs:'+str(result)+' .Does the SQL and output directly satisfy the user\'s needs? and outputs only whether or not it is satisfied. Output Satisfaction Score(1~10) without any explanation only in a json format:{"score":""}'
    return question

# ——————————————————
# pipeline
# 下的各种prompt:
# ——————————————————
from tools.template import template_dict 

def get_answer(previous,question,db_name,domain_knowledge,template_name):
    
    template = template_dict[template_name]
    template_name = template.template_name
    system_format = template.system_format
    user_format = template.user_format
    assistant_format = template.assistant_format
    system = template.system

    description = bird_getdesc(db_name)

    behaviors = '''The user question type can be the following dialogue behaviors:
INFORM SQL: Users provide requests through natural language question. If the user's question can be answered through SQL, the system needs to write SQL and explain（dont need to explain based on the SQL results）
INFER SQL: If the user's question must be answered through SQL and human inference. For example, if the user's question is a "yes/no" question, or about "the third oldest...", SQL cannot return the answer directly (or is too complex), but we can infer the answer based on the SQL results.
AMBIGUOUS: The user's question is ambiguous and the system needs to reconfirm the user's intent (e.g., "Did you mean...?") or ask the user to specify which columns or values to return.
CANNOT_ANSWER: The question contains additional information not found in the database. (When the user is unfamiliar with the database schema or its implications) The system cannot easily answer the user's question via SQL, and the system informs the user of its limitations.The system needs to detect what information the user needs but is not included in the database.
IMPROPER:Inappropriate questions, such as small talk or questions asking for advice.The system should answer smooth and reasonable daily answers
    '''
    
    system_text = system_format.format(content=(behaviors+'Provide an appropriate response to the current question based on the tables description Domain knowledge and previous conversations, noting if the question is ambiguous or unanswerable. \n tables description:'+str(description)+' Domain knowledge:'+str(domain_knowledge)))+'\nAnswer the user in json format\{"type":""(INFORM_SQL/INFER_SQL/CANNOT_ANSWER/AMBIGUOUS/IMPROPER), "sql":""(Omit this field if it cannot be generated),"text":""(system natural language reply)\}'

    pre = ""

    for item in previous:
        user = user_format.format(content=item['question'])
        assistant = assistant_format.format(content='{"type":"'+str(item['type'])+'","sql":"'+str(item['sql'])+'","text":"'+str(item['answer'])+'"} ')
        pre = pre+user+assistant
        if item['result']:
            pre += 'the result of the sql:'+str(item['result'])
    
    question=system_text+pre+user_format.format(content=str(question))

   
    
    return question