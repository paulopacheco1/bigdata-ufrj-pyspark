import PyPDF2
import re
import json
# import pymongo
import time
from pyspark import SparkContext, SparkConf

time.sleep(10)

# sc = SparkContext('local[*]')
conf = SparkConf()
conf.setMaster('spark://spark:7077')
sc = SparkContext(conf=conf)

tribunal = 'Tribunal de Justiça do Rio de Janeiro'
comarca = 'Campo Grande'
uf = 'RJ'

pdf_file = open('./20211110CAPDJETJRJ.pdf', 'rb')

read_pdf = PyPDF2.PdfFileReader(pdf_file)

number_of_pages = read_pdf.getNumPages()

array = []

def replaceName(text):
    dicionario = {
        'Despacho',
        'Interessado',
        'Síndico'
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
    
        partes = processoText[26:processoText[26:].find(':')+26].split(' X ')
        
        aPartes = []

        numberProcessoOld = ''

        for parte in partes:

            parte = replaceName(parte.replace('-','').strip())

            nome = parte[0:parte[0:].find('(Adv(s).')].strip()
            
            if(nome.find('(') != -1):               
                numberProcessoOld = nome[1:17]
                nome = nome[18:].strip()

                advogados = parte[parte[0:].find('(Adv(s).'):].split(',')
            
                aAdvogados = []

                for advogado in advogados:
                
                    advogado = advogado.replace('Dr(a).','').strip()          
                    advogado = advogado.replace('(Adv(s).','').strip()              

                    nomeAdvogado= advogado[0:advogado.find('(')+1].strip()
                    oab = advogado[advogado.find('(OAB/')+5:advogado.find(')')].strip()

                    if(nomeAdvogado): 
                        aAdvogados.append({
                            'nome':nomeAdvogado,
                            'oab':oab
                        })
                
                aPartes.append(
                    {
                        'nome':nome,
                        'advogados':aAdvogados
                    }
                )    
    
        aAndamento = processoText.split(':')

        andamentoCount = len(aAndamento)

        tipoAndamento = ''
        descricaoAndamento = ''

        if(andamentoCount == 2):
            tipoAndamento = aAndamento[0].strip()
            descricaoAndamento = aAndamento[1].strip()
        
        if(andamentoCount == 3):
            tipoAndamento = aAndamento[1].strip()
            descricaoAndamento = aAndamento[2].strip()
        

        if(andamentoCount == 4):
            tipoAndamento = aAndamento[2].strip()
            descricaoAndamento = aAndamento[3].strip()

        # if(tipoAndamento):
        #     print(x,len(tipoAndamento))
        #     if(len(tipoAndamento) > 1):
        #         tipoAndamento = tipoAndamento.rsplit(' ', 1)[1]

        return {
                'numJustica':numberProcesso,
                'partes':aPartes,
                'numJusticaAntigo':numberProcessoOld,
                'andamentos':[{
                    'tipo':tipoAndamento,
                    'descricao':descricaoAndamento
                }],
                'tribunal':tribunal,
                'comarca':comarca,
                'uf':uf
            }

# for x in range(10):
for x in range(number_of_pages):
    
    page = read_pdf.getPage(x)

    #extrai apenas o texto
    page_content = page.extractText()

    # faz a junção das linhas 
    parsed = ''.join(page_content)

    # remove as quebras de linha
    parsed = re.sub('\n', '', parsed)

    processos = sc.parallelize(parsed.split('Proc.')).map(scrapProcesso).collect()

    array.append(processos)

print(array)

