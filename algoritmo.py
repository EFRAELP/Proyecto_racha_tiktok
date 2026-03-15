def calcular_plan(biblioteca):
    """
    Greedy set cover: encuentra el mínimo de videos que cubran a todos los contactos.
    Retorna (plan, sin_cobertura) donde:
      - plan: lista de {"video": ..., "enviar_a": [...]}
      - sin_cobertura: contactos sin ningún video asignado
    """
    todos = set()
    for v in biblioteca:
        for c in v.get("para", []):
            todos.add(c)

    pendientes = set(todos)
    resultado = []
    disponibles = [dict(v, _para_set=set(v.get("para", []))) for v in biblioteca]

    while pendientes:
        mejor = max(
            disponibles,
            key=lambda x: len(x["_para_set"] & pendientes),
            default=None,
        )
        if not mejor or not (mejor["_para_set"] & pendientes):
            break

        efectivos = sorted(mejor["_para_set"] & pendientes)
        resultado.append({
            "video": {k: v for k, v in mejor.items() if k != "_para_set"},
            "enviar_a": efectivos,
        })
        pendientes -= set(efectivos)
        disponibles.remove(mejor)

    return resultado, sorted(pendientes)
