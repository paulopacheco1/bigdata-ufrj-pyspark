import PyPDF2
import re
import json
import pymongo
import time
from pyspark import SparkContext, SparkConf

time.sleep(5)

# sc = SparkContext('local[*]')
conf = SparkConf()
conf.setMaster('spark://spark:7077')
sc = SparkContext(conf=conf)

# myclient = pymongo.MongoClient("mongodb+srv://admin:admin1324@bigdataufrj.lpm6m.mongodb.net/projetoBigData?retryWrites=true&w=majority")
myclient = pymongo.MongoClient("mongodb://admin:admin1324@mongo:27017/projetoBigData?authSource=admin")
mydb = myclient["projetoBigData"]
mycol = mydb["processos"]

pdf_file = open('./20211110CAPDJETJRJ.pdf', 'rb')
read_pdf = PyPDF2.PdfFileReader(pdf_file)
number_of_pages = read_pdf.getNumPages()

tribunal = 'Tribunal de Justiça do Rio de Janeiro'
uf = 'RJ'

def replaceName(text):
    dicionario = {
        'Despacho',
        'Interessado',
        'Síndico',
        'Sentença'
    }

    frase = text

    for palavra in dicionario:
        frase = frase.replace(palavra,'')
    return frase

def isNumProcesso(cpf):
    pattern = r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$"
    return bool(re.match(pattern, cpf))

def scrapProcesso(processoText):
    numberProcesso = processoText[1:26]
        
    if (isNumProcesso(numberProcesso) == True):   
        print("============PROCESSO ("+numberProcesso+")===========")
        partes = processoText[26:].split(' X ')
        
        andamento = processoText[26:]
        numberProcessoOld  = ''
        aPartes = []         

        temporario = andamento.split('(OAB/')
        andamento = temporario[-1]  
        andamento = andamento.replace('-','').replace('(','').replace(')','').strip()

        for parte in partes:
            
            parte = parte.replace('-','').strip()
            
            nome = ''

            aAdvogados = []
            sAdvogados = ''
            
            if(parte.find('(') != -1):
                if(parte[0] == '('):
                    numberProcessoOld = parte[1:17] 
                    if(parte[18:].find('(') != -1):     
                        nome = parte[18:parte[18:].index('(')+18].strip()        
                        sAdvogados = parte[parte[18:].index('(')+18:]   
                                
                else:
                    nome = parte[0:parte.index('(')].strip()
                    sAdvogados = parte[parte.index('('):]
                    

                
                if(sAdvogados.find('(Adv(s).') != -1):
                    sAdvogados = sAdvogados.replace('(Adv(s).','').strip()

                if(sAdvogados.find('Dr(a).') != -1):
                    sAdvogados = sAdvogados.replace('Dr(a).','').strip()
                    
                advogados = sAdvogados.split(',')
                
                for advogado in advogados:
                    if(advogado.find('OAB/') != -1):
                        if(advogado.find(')') != -1):
                            advogado = advogado[0:advogado.index(')')+1].strip()
                            
                            advogado = advogado.split('(')
                            nomeAdvogado= advogado[0].replace(':','').strip()

                            oab = ''
                            
                            if(len(advogado) > 1):
                                if(advogado[1].find(')') != -1):
                                    oab = advogado[1].replace(')','').replace('OAB/','').strip()
                                
                                if(oab.find('OAB/') != -1):
                                    oab = oab.replace('OAB/','').strip()
                            
                            andamento = andamento.replace(oab,'').replace(nomeAdvogado,'').strip()

                            if(len(nomeAdvogado) > 0): 
    
                                aAdvogados.append({
                                    'nome':nomeAdvogado,
                                    'oab':oab
                                })     
            else:
                if(parte[0:].find(':') != -1):
                    nome = parte[0:parte.index(':')]
                else:
                    nome = parte[0:]

            nome = replaceName(nome) 
            andamento = andamento.replace(nome,'').replace("X",'').strip()

            if(len(nome) > 0): 
                aPartes.append(
                    {
                        'nome':nome,
                        'advogados':aAdvogados
                    }
                )    

        return {
                    'numJustica':numberProcesso,
                    'partes':aPartes,
                    'numJusticaAntigo':numberProcessoOld,
                    'andamentos':[{'descricao':andamento}],
                    'tribunal':tribunal,
                    'uf':uf
        }

print(number_of_pages)
for x in range(number_of_pages):
    page = read_pdf.getPage(x)

    #extrai apenas o texto
    page_content = page.extractText()

    # faz a junção das linhas 
    parsed = ''.join(page_content)

    # remove as quebras de linha
    parsed = re.sub('\n', '', parsed)

    # separa os processos
    parsed = parsed.split('Proc.')

    processos = sc \
        .parallelize(parsed) \
        .map(scrapProcesso) \
        .collect()

    for processo in processos:
        if processo is None:
            continue

        processoJaExiste = mycol.count_documents({ "numJustica": processo["numJustica"] }) > 0
        if not processoJaExiste:
            mycol.insert_one(processo)
