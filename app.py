import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QDate
from PyQt5.uic import loadUi

from datetime import datetime
from dateutil.relativedelta import relativedelta

# ----------------------------------------
# Tabela da prescrição 
# (podendo ser reduzida pela metade)
#     
# [0] Pena < 1 ano             --> 3 anos
# [1] 1 ano <= Pena < 2 anos   --> 4 anos
# [2] 2 anos < Pena <= 4 anos  --> 8 anos
# [3] 4 anos < Pena <= 8 anos  --> 12 anos
# [4] 8 anos < Pena <= 12 anos --> 16 anos
# [5] Pena > 12 anos           --> 20 anos  
# ----------------------------------------

# Classe herdando QMainWindows
class Prescricao(QMainWindow):

    def __init__(self):
        super().__init__()
        
        # Carrega a interface
        loadUi(r'interfaces\tela_01.ui', self)
        
        # Seta os campos de datas
        self.dateEdit_2RecDen.setDate(QDate.currentDate())
        self.dateEdit_3InicioSusp.setDate(QDate.currentDate())
        self.dateEdit_3InicioSusp.setEnabled(False)
        self.dateEdit_4FimSusp.setDate(QDate.currentDate())
        self.dateEdit_4FimSusp.setEnabled(False)

        # Calcula a prescrição ou sai do programa
        self.pushButtonCalc.clicked.connect(self.calcula_prescricao)
        self.pushButton_2Sair.clicked.connect(self.close)
        
        # Controle de ativação/desativação dos campos das datas
        self.checkBoxInicSusp.stateChanged.connect(self.checkBoxInicSusp_StateChanged)  
        self.checkBox_2FimSusp.stateChanged.connect(self.checkBox_2FimSusp_StateChanged)

    def checkBoxInicSusp_StateChanged(self, state):
        if state == QtCore.Qt.Checked:
            self.dateEdit_3InicioSusp.setEnabled(True)
            self.checkBox_2FimSusp.setEnabled(True)
        else:
            self.dateEdit_3InicioSusp.setEnabled(False)
            self.dateEdit_4FimSusp.setEnabled(False)
            self.checkBox_2FimSusp.setEnabled(False)
            self.checkBox_2FimSusp.setChecked(False)

    def checkBox_2FimSusp_StateChanged(self, state):
        if state == QtCore.Qt.Checked:
            self.dateEdit_4FimSusp.setEnabled(True)
            self.checkBoxInicSusp.setChecked(True)
        else:
            self.dateEdit_4FimSusp.setEnabled(False)   
 
    def calcula_prescricao(self):
        data_hoje = datetime.now()
        selecao_combo = self.comboBoxPena.currentIndex()
        data_fato = converte_data(self.dateEditFato.date())
        data_receb_den = converte_data(self.dateEdit_2RecDen.date())
        data_inicio_susp = converte_data(self.dateEdit_3InicioSusp.date())
        data_fim_susp = converte_data(self.dateEdit_4FimSusp.date())
        check_inicio_susp = self.checkBoxInicSusp.isChecked()
        check_fim_susp = self.checkBox_2FimSusp.isChecked()
        check_metade = self.checkBoxMetade.isChecked()

        tabela_prescricao = {
            0:relativedelta(years=3),
            1:relativedelta(years=4),
            2:relativedelta(years=8),
            3:relativedelta(years=12),
            4:relativedelta(years=16),
            5:relativedelta(years=20)  
            }

        tabela_prescricao_metade = {
            0:relativedelta(years=1, months=6),
            1:relativedelta(years=2),
            2:relativedelta(years=4),
            3:relativedelta(years=6),
            4:relativedelta(years=8),
            5:relativedelta(years=10)  
            }
 
        if check_metade:
             tempo_prescricao = tabela_prescricao_metade[selecao_combo]
        else:
             tempo_prescricao = tabela_prescricao[selecao_combo]

        # Controles
        criterio_0 = (data_hoje >= data_fato)
        criterio_1 = (data_fato <= data_receb_den)
        criterio_2 = (data_receb_den <= data_inicio_susp)
        criterio_3 = (data_inicio_susp <= data_fim_susp)

        # Caso base
        data_prescricao = data_fato + tempo_prescricao + relativedelta(days=-1)
        data_prescricao_apos_receb = data_receb_den + tempo_prescricao + relativedelta(days=-1)

        # Verificação inicial
        if not (criterio_0 and criterio_1 and criterio_2 and criterio_3):
             mensagem = "Verifique as datas!"
             exibe_critico(self, mensagem)
        
        # Prescrição antes do recebimento da denúncia
        elif data_receb_den > data_prescricao:
            mensagem = f'A prescrição ocorreu em {data_prescricao.strftime("%d/%m/%Y")}!'
            exibe_advertencia(self, mensagem)

        # Prescrição antes da suspensão
        elif data_inicio_susp > data_prescricao_apos_receb:
            mensagem = f'A prescrição ocorreu em {data_prescricao_apos_receb.strftime("%d/%m/%Y")}!'
            exibe_advertencia(self, mensagem)
            
        # Prescrição sem suspensão do processo
        elif (not check_inicio_susp) and (not check_fim_susp):
            mensagem = f'A prescrição ocorre em {data_prescricao_apos_receb.strftime("%d/%m/%Y")}!'
            exibe_advertencia(self, mensagem)

        # Prescrição com processo suspenso
        elif check_inicio_susp and (not check_fim_susp):
            dias_entre_receb_e_susp = data_inicio_susp - data_receb_den
            data_fim_susp = data_inicio_susp + tempo_prescricao + relativedelta(days=-1)
            data_prescricao = data_fim_susp + tempo_prescricao - dias_entre_receb_e_susp + relativedelta(days=-1)
            mensagem = f'O processo tramitou {dias_entre_receb_e_susp.days} dias entre o recebimento e o início da suspensão.\n'
            mensagem += f'Início da suspensão: {data_inicio_susp.strftime("%d/%m/%Y")}\n'
            mensagem += f'Data calculada para o fim da suspensão: {data_fim_susp.strftime("%d/%m/%Y")}\n'
            mensagem += f'O processo fica(ou) suspenso até {data_fim_susp.strftime("%d/%m/%Y")}.\n'
            mensagem += f'A prescrição ocorre(rá) em {data_prescricao.strftime("%d/%m/%Y")}!'
            exibe_advertencia(self, mensagem)

        # Prescrição com início e fim da suspensão
        else:
            if data_hoje + (data_fim_susp - data_inicio_susp) >= data_hoje + tempo_prescricao:
                mensagem = "Verifique o tempo total em que o processo permaneceu suspenso!"
                exibe_critico(self, mensagem)

            else:
                dias_entre_receb_e_susp = data_inicio_susp - data_receb_den
                data_prescricao = data_fim_susp + tempo_prescricao - dias_entre_receb_e_susp + relativedelta(days=-1)
                mensagem = f'O processo tramitou {dias_entre_receb_e_susp.days} dias entre o recebimento e o início da suspensão.\n'
                mensagem += f'Início da suspensão: {data_inicio_susp.strftime("%d/%m/%Y")}\n'
                mensagem += f'Fim da suspensão: {data_fim_susp.strftime("%d/%m/%Y")}\n'
                mensagem += f'O processo ficou suspenso por {(data_fim_susp - data_inicio_susp).days} dias.\n'
                mensagem += f'#5 - A prescrição ocorre em {data_prescricao.strftime("%d/%m/%Y")}!' 
                exibe_advertencia(self, mensagem)
    
def exibe_advertencia(self, mensagem):
    QMessageBox.warning(
        self,
        "Atenção!",
        mensagem,
        QMessageBox.Ok
    )

def exibe_critico(self, mensagem):
    QMessageBox.critical(
        self,
        "Atenção!",
        mensagem,
        QMessageBox.Ok
    )

def converte_data(q_data):
    """Converte a data capturada pelo campo para o formato datetime"""
    year = q_data.year()
    month = q_data.month()
    day = q_data.day()
    data = datetime(year, month, day)
    return data

def sair():
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    programa = Prescricao()
    programa.show()
    sys.exit(app.exec_())