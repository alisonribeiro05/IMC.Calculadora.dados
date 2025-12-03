import tkinter as tk
from tkinter import ttk, messagebox, Tk, Toplevel  # Importado Toplevel
import sqlite3
from datetime import datetime


# --- Configuração do Banco de Dados SQLite ---

def inicializar_bd():
    """Cria a tabela de pacientes se ela não existir."""
    conn = sqlite3.connect('imc_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            altura_cm REAL NOT NULL,
            peso_kg REAL NOT NULL,
            imc REAL NOT NULL,
            classificacao TEXT NOT NULL,
            data_calculo TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def salvar_resultado(nome, altura_cm, peso_kg, imc, classificacao):
    """Insere o resultado do cálculo no banco de dados."""
    try:
        conn = sqlite3.connect('imc_data.db')
        cursor = conn.cursor()
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO pacientes (nome, altura_cm, peso_kg, imc, classificacao, data_calculo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, altura_cm, peso_kg, imc, classificacao, data_hora))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        messagebox.showerror("Erro de Banco de Dados", f"Não foi possível salvar os dados: {e}")


# --- Funções da Aplicação ---

def calcular_imc():
    try:
        nome = entry_nome.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Por favor, insira o nome do paciente.")
            return

        altura_cm = float(entry_altura.get().replace(',', '.'))
        peso_kg = float(entry_peso.get().replace(',', '.'))

        if altura_cm <= 0 or peso_kg <= 0:
            messagebox.showwarning("Aviso", "Altura e Peso devem ser valores positivos.")
            return

        altura_m = altura_cm / 100.0
        imc = peso_kg / (altura_m ** 2)

        if imc < 18.5:
            classificacao = "Magreza"
        elif 18.5 <= imc <= 24.9:
            classificacao = "Peso Normal"
        elif 25.0 <= imc <= 29.9:
            classificacao = "Sobrepeso"
        elif 30.0 <= imc <= 39.9:
            classificacao = "Obesidade"
        else:
            classificacao = "Obesidade Grave"

        # Salva o resultado no banco de dados
        salvar_resultado(nome, altura_cm, peso_kg, imc, classificacao)

        # Exibe o resultado na GUI
        resultado_texto = (
            f"Paciente: {nome}\n"
            f"IMC Calculado: {imc:.2f} kg/m²\n"
            f"Classificação: {classificacao}"
        )

        text_resultado.config(state=tk.NORMAL)
        text_resultado.delete("1.0", tk.END)
        text_resultado.insert(tk.END, resultado_texto)
        text_resultado.config(state=tk.DISABLED)

    except ValueError:
        messagebox.showerror("Erro de Entrada", "Por favor, insira valores numéricos válidos para Altura e Peso.")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")


# --- NOVA FUNÇÃO: CONSULTAR PACIENTE ---

def consultar_paciente():
    """Busca no banco de dados o histórico de IMC para o nome inserido e exibe em uma nova janela."""
    nome = entry_nome.get().strip()
    if not nome:
        messagebox.showwarning("Aviso",
                               "Por favor, insira o nome do paciente para consulta no campo 'Nome do Paciente'.")
        return

    try:
        conn = sqlite3.connect('imc_data.db')
        cursor = conn.cursor()

        # Consulta todos os registros para o nome fornecido, ordenando pelo mais recente
        # Uso de LIKE com '%' permite a busca parcial (ex: buscar 'Maria' encontra 'Maria Silva')
        cursor.execute("""
            SELECT altura_cm, peso_kg, imc, classificacao, data_calculo 
            FROM pacientes 
            WHERE nome LIKE ? 
            ORDER BY data_calculo DESC
        """, ('%' + nome + '%',))

        registros = cursor.fetchall()
        conn.close()

        if not registros:
            messagebox.showinfo("Consulta", f"Nenhum registro encontrado para o paciente que contém '{nome}'.")
            return

        # 1. Cria a janela Toplevel para o histórico
        janela_consulta = tk.Toplevel(janela)
        janela_consulta.title(f"Histórico de IMC - {nome.upper()}")
        janela_consulta.transient(janela)
        janela_consulta.grab_set()

        frame_consulta = ttk.Frame(janela_consulta, padding="10")
        frame_consulta.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 2. Prepara o texto de exibição
        texto_historico = f"Histórico de Cálculos de IMC para: {nome.upper()}\n"
        texto_historico += "=" * 55 + "\n"

        num_registros = len(registros)
        for i, reg in enumerate(registros):
            altura, peso, imc, classificacao, data_calculo = reg

            # Formatação da data
            data_obj = datetime.strptime(data_calculo, "%Y-%m-%d %H:%M:%S")
            data_formatada = data_obj.strftime("%d/%m/%Y às %H:%M")

            texto_historico += f"--- Registro #{num_registros - i} ({data_formatada}) ---\n"
            texto_historico += f"  Altura: {altura:.0f} cm\n"
            texto_historico += f"  Peso: {peso:.2f} kg\n"
            texto_historico += f"  IMC: {imc:.2f} kg/m²\n"
            texto_historico += f"  Classificação: {classificacao}\n"
            texto_historico += "-" * 55 + "\n"

        # 3. Cria e insere o texto em um widget Text com Scrollbar
        text_historico = tk.Text(frame_consulta, height=20, width=60, wrap=tk.WORD)
        text_historico.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        text_historico.insert(tk.END, texto_historico)
        text_historico.config(state=tk.DISABLED)

        scrollbar = ttk.Scrollbar(frame_consulta, command=text_historico.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        text_historico['yscrollcommand'] = scrollbar.set

        janela_consulta.protocol("WM_DELETE_WINDOW",
                                 lambda: [janela_consulta.grab_release(), janela_consulta.destroy()])
        janela_consulta.wait_window()

    except sqlite3.Error as e:
        messagebox.showerror("Erro de Banco de Dados", f"Erro ao consultar o histórico: {e}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")


def reiniciar_campos():
    entry_nome.delete(0, tk.END)
    entry_altura.delete(0, tk.END)
    entry_peso.delete(0, tk.END)

    text_resultado.config(state=tk.NORMAL)
    text_resultado.delete("1.0", tk.END)
    text_resultado.config(state=tk.DISABLED)


def sair_aplicacao():
    janela.quit()


# --- Configuração da Janela (Atualizada) ---

janela: Tk = tk.Tk()
janela.title("Cálculo do IMC - Índice de Massa Corporal")

# Inicializa o banco de dados antes de iniciar a GUI
inicializar_bd()

frame_principal = ttk.Frame(janela, padding="10")
frame_principal.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Campos de Entrada
label_nome = ttk.Label(frame_principal, text="Nome do Paciente:")
label_nome.grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
entry_nome = ttk.Entry(frame_principal, width=50)
entry_nome.grid(row=0, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)

label_altura = ttk.Label(frame_principal, text="Altura (cm):")
label_altura.grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
entry_altura = ttk.Entry(frame_principal, width=15)
entry_altura.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

label_peso = ttk.Label(frame_principal, text="Peso (Kg):")
label_peso.grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
entry_peso = ttk.Entry(frame_principal, width=15)
entry_peso.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

# Área de Resultado
label_resultado_titulo = ttk.Label(frame_principal, text="Resultado", anchor=tk.CENTER)
label_resultado_titulo.grid(row=1, column=2, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)

text_resultado = tk.Text(frame_principal, height=5, width=30, wrap=tk.WORD)
text_resultado.grid(row=2, column=2, columnspan=2, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
text_resultado.config(state=tk.DISABLED)

# --- Botões (Nova Organização) ---
# Linha 4 agora contém 4 botões para funcionalidade completa

button_calcular = ttk.Button(frame_principal, text="Calcular", command=calcular_imc)
button_calcular.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=5, pady=10)

button_reiniciar = ttk.Button(frame_principal, text="Reiniciar", command=reiniciar_campos)
button_reiniciar.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=10)

button_consultar = ttk.Button(frame_principal, text="Consultar", command=consultar_paciente)
button_consultar.grid(row=4, column=2, sticky=(tk.W, tk.E), padx=5, pady=10)

button_sair = ttk.Button(frame_principal, text="Sair", command=sair_aplicacao)
button_sair.grid(row=4, column=3, sticky=(tk.W, tk.E), padx=5, pady=10)

frame_principal.grid_columnconfigure(1, weight=1)
frame_principal.grid_columnconfigure(2, weight=1)

if __name__ == "__main__":
    janela.mainloop()
