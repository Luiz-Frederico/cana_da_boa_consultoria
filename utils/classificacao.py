def classificar_por_probabilidade(probabilidade: float) -> str:
    if probabilidade >= 96:
        return "RISCO MINIMO"
    elif probabilidade >= 86:
        return "RISCO MUITO BAIXO"
    elif probabilidade >= 76:
        return "RISCO BAIXO"
    elif probabilidade >= 67:
        return "RISCO MEDIO/BAIXO"
    elif probabilidade >= 51:
        return "RISCO MEDIO"
    elif probabilidade >= 31:
        return "RISCO ALTO"
    else:
        return "RISCO ALTISSIMO"