from ui.console_menu import Menu, solicitar_e_conectar_oracle

if __name__ == "__main__":
    app = Menu()
    
    # Obtém o service para a conexão inicial (se desejar)
    service = app.get_service()
    
    # Tenta conectar automaticamente (mesmo comportamento anterior)
    solicitar_e_conectar_oracle(service)
    
    try:
        app.exibir()
    except KeyboardInterrupt:
        app._sair()