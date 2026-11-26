\# LifeOS AI



\*\*Sistema inteligente de gerenciamento pessoal com integração entre Inteligência Artificial, Python, Ollama e Notion.\*\*



\## 1. Visão geral



O LifeOS AI é uma aplicação desenvolvida em Python que utiliza um modelo de linguagem local para atuar como assistente de planejamento e acompanhamento de tarefas.



O sistema integra dados armazenados no Notion com processamento local por meio do Ollama, permitindo consultar metas, acompanhar atividades, calcular indicadores e atualizar o andamento das tarefas por meio de uma interface conversacional.



\## 2. Objetivo



Desenvolver um assistente inteligente capaz de centralizar o acompanhamento de metas e tarefas, transformar informações em indicadores de progresso e permitir interações em linguagem natural.



\## 3. Funcionalidades implementadas



\- Integração com a API do Notion.

\- Consulta de metas e planos de ação.

\- Identificação da próxima tarefa.

\- Cálculo automático de indicadores de desempenho.

\- Acompanhamento de tarefas pendentes, concluídas e em andamento.

\- Identificação de atividades atrasadas.

\- Atualização de status de tarefas no Notion mediante confirmação do usuário.

\- Integração com modelo de linguagem local.

\- Memória persistente das conversas.



\## 4. Arquitetura do projeto



O projeto utiliza uma arquitetura modular, separando a interface principal das integrações externas.



```text

LifeOS-AI/

│

├── app/

│   ├── \_\_init\_\_.py

│   ├── notion\_client.py

│   └── ollama\_client.py

│

├── main.py

├── requirements.txt

├── .gitignore

└── README.md

```



\*\*Responsabilidades dos módulos:\*\*



\- `main.py`: fluxo principal da aplicação, indicadores, memória e interação com o usuário.

\- `notion\_client.py`: comunicação com a API do Notion e gerenciamento das tarefas.

\- `ollama\_client.py`: comunicação com o modelo de linguagem local.

\- `requirements.txt`: dependências Python do projeto.



\## 5. Tecnologias utilizadas



| Tecnologia | Aplicação |

|---|---|

| Python | Desenvolvimento da aplicação |

| Ollama | Execução local de modelos de linguagem |

| Mistral | Modelo de linguagem utilizado |

| Notion API | Armazenamento e atualização de tarefas |

| Requests | Comunicação HTTP |

| Python-dotenv | Gerenciamento de variáveis de ambiente |



\## 6. Requisitos



\- Python 3.12 ou superior.

\- Ollama instalado.

\- Modelo Mistral disponível localmente.

\- Conta no Notion.

\- Integração do Notion com acesso às bases utilizadas pelo projeto.



\## 7. Instalação



Clone o repositório:



```bash

git clone https://github.com/itpamis/LifeOS-AI.git

cd LifeOS-AI

```



Crie um ambiente virtual:



```bash

py -m venv .venv

```



Ative o ambiente:



```bash

.venv\\Scripts\\activate

```



Instale as dependências:



```bash

pip install -r requirements.txt

```



\## 8. Configuração



Crie um arquivo `.env` na raiz do projeto:



```env

NOTION\_TOKEN=seu\_token\_de\_integracao

NOTION\_VERSION=2026-03-11

```



Utilize seu próprio token de integração e conceda acesso às bases do Notion.



O arquivo `.env` não deve ser publicado no GitHub.



\## 9. Execução



Certifique-se de que o Ollama esteja em execução e que o modelo Mistral utilizado pelo projeto esteja disponível.



Execute:



```bash

ollama list

```



Em seguida, inicie a aplicação:



```bash

py main.py

```



\## 10. Fluxo de funcionamento



1\. A aplicação consulta as metas e tarefas no Notion.

2\. Os dados são processados para calcular indicadores.

3\. O sistema identifica a próxima tarefa e apresenta o planejamento.

4\. O usuário interage com o assistente por linguagem natural.

5\. O modelo local interpreta as solicitações e utiliza o contexto do planejamento.

6\. Quando uma alteração de status é solicitada, o sistema apresenta a mudança e solicita confirmação.

7\. Após a confirmação, a aplicação atualiza o Notion e recalcula os indicadores.



\## 11. Segurança



\- Tokens e credenciais são armazenados em variáveis de ambiente.

\- O arquivo `.env` é excluído do versionamento.

\- A memória local e os arquivos de ambiente virtual não são publicados.

\- Alterações de status exigem confirmação explícita do usuário.



\## 12. Melhorias futuras



\- Registro de horas efetivamente trabalhadas.

\- Análise de produtividade e estimativas.

\- Replanejamento automático de atividades.

\- Dashboard visual de metas e indicadores.

\- Expansão da memória contextual.



\## 13. Autor



Projeto desenvolvido como iniciativa de aplicação prática de Inteligência Artificial, automação e integração de sistemas.



\*\*GitHub:\*\* https://github.com/itpamis/LifeOS-AI



\---



\*LifeOS AI — Inteligência Artificial aplicada à organização e gestão pessoal.\*

