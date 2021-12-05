import PyPDF2
import re
import json
import pymongo

tribunal = 'Tribunal de Justiça do Rio de Janeiro'
uf = 'RJ'

pdf_file = open('./20211110CAPDJETJRJ.pdf', 'rb')

read_pdf = PyPDF2.PdfFileReader(pdf_file)

number_of_pages = read_pdf.getNumPages()

array = []

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

#myclient = pymongo.MongoClient("mongodb+srv://admin:admin1324@bigdataufrj.lpm6m.mongodb.net/projetoBigData?retryWrites=true&w=majority")
#mydb = myclient["projetoBigData"]

#mycol = mydb["processos"]

for x in range(1):
    page = read_pdf.getPage(13)

    #extrai apenas o texto
    page_content = page.extractText()

    # faz a junção das linhas 
    parsed = ''.join(page_content)

    # remove as quebras de linha
    parsed = re.sub('\n', '', parsed)

    processos = parsed.split('Proc.')

    for processo in processos:
        numberProcesso = processo[1:26]
        
        if (isNumProcesso(numberProcesso) == True):   
            print("============PROCESSO ("+numberProcesso+")===========")
            partes = processo[26:].split(' X ')

           
            andamento = processo[26:]
            numberProcessoOld  = ''
            aPartes = []         

            temporario = andamento.split('(OAB/')
            andamento = temporario[-1]  
            andamento = andamento.replace('-','').replace('(','').replace(')','').strip()

            for parte in partes:
               
                parte = parte.replace('-','').strip()
               
                nome = ''

                aAdvogados = []

               

                if(parte.find('(') != -1):
                    if(parte[0] == '('):
                       numberProcessoOld = parte[1:17]      
                       nome = parte[18:parte[18:].index('(')+18].strip()        
                       advogados = parte[parte[18:].index('(')+18:]                  
                    else:
                        nome = parte[0:parte.index('(')].strip()
                        advogados = parte[parte.index('('):]

                    advogados = advogados.replace('(Adv(s).','').replace('Dr(a).','').strip()
                        
                    advogados = advogados.split(',')
                    
                    for advogado in advogados:
                        if(advogado.find('OAB/') != -1):
                            advogado = advogado[0:advogado.index(')')+1].strip()
                            
                            advogado = advogado.split('(')
                            nomeAdvogado= advogado[0].replace(':','').strip()
                            oab = advogado[1].replace(')','').replace('OAB/','').strip()
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
            
            print({
                'numJustica':numberProcesso,
                'partes':aPartes,
                'numJusticaAntigo':numberProcessoOld,                
                'tribunal':tribunal,
                'uf':uf,
                'andamentos':[{andamento}]
            })
            
        

            
           
