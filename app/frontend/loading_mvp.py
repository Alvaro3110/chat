import streamlit as st
import time
import random

def mock_agent_logic(prompt):
    """
    Simula um agente real gerando pensamentos dinâmicos 
    baseados no input do usuário.
    """
    context_thoughts = [
        f"Recebi a solicitação sobre: '{prompt}'.",
        "Iniciando varredura nos metadados do grupo econômico...",
        "Detectei necessidade de análise de risco de crédito setorial.",
        "Avaliando se há dados suficientes para uma projeção de 12 meses.",
        "Cruzando dados de faturamento com o rating atual do cliente.",
        "Sintetizando recomendações para o comitê de crédito."
    ]
    
    # Simula o agente 'escrevendo' seus pensamentos
    for thought in context_thoughts:
        yield thought
        time.sleep(random.uniform(0.5, 1.2))

def loading_mvp_v4():
    st.title("MVP v4: Raciocínio Dinâmico do Agente")
    st.markdown("""
    Este exemplo demonstra como capturar o raciocínio **gerado pelo agente** 
    em tempo real, sem textos fixos (hardcoded) no frontend.
    """)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if "thought" in msg:
                with st.expander("🧠 Raciocínio Dinâmico do Agente", expanded=False):
                    st.markdown(msg["thought"])
            st.write(msg["content"])

    if prompt := st.chat_input("Pergunte ao agente..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        full_thought = ""
        
        with st.status("Agente em reflexão...", expanded=True) as status:
            st.write("⚙️ Orquestrador iniciado.")
            
            thought_placeholder = st.empty()
            st.markdown("---")
            st.caption("FLUXO DE PENSAMENTO DO AGENTE:")
            
            # Capturando o raciocínio vindo da 'lógica do agente'
            for dynamic_thought in mock_agent_logic(prompt):
                full_thought += f"> {dynamic_thought}\n\n"
                thought_placeholder.markdown(full_thought)
            
            st.markdown("---")
            status.update(label="Raciocínio concluído!", state="complete", expanded=False)

        response = f"Análise concluída para o seu pedido."
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "thought": full_thought
        })
        
        with st.chat_message("assistant"):
            st.write(response)
            
        st.rerun()

if __name__ == "__main__":
    loading_mvp_v4()
