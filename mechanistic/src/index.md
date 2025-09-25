---
marp: true
theme: default
paginate: true
math: katex
class: lead
size: 16:9
title: "Mechanistic Interpretability de Transformers"
description: "Una introducción práctica y teórica a interpretabilidad mecanicista."
footer: "Mechanistic Interpretability · Oscar Stanchi"
---

# Mechanistic Interpretability

**Objetivo del curso**  
Entender, con *reverse engineering*, qué **algoritmos internos** aprenden los *transformers* y **cómo** contribuyen a sus predicciones.  

---

`img/mech_tag_cloud.png`

---

## Agenda

1) Introducción y motivaciones  
2) Recordatorio: arquitectura *Transformer* (decoder-only)  
3) Conceptos base de **Mechanistic Interpretability**  
4) Patrones y **circuitos** (Induction, QK/OV)  
5) Caso de estudio: **IOI** (*Indirect Object Identification*)  
6) **Superposición** (*Superposition*) y *toy models*  
7) **Sparse Autoencoders (SAE)** y monosemanticidad  
8) Limitaciones, riesgos y lecturas

---

## Motivación

- Modelos potentes, pero de **caja negra**. Necesitamos *mechanistic interpretability* para:
  - **Confiabilidad** y *debugging*.
  - **Seguridad** y alineamiento.
  - Transferir conocimiento entre tareas/modelos.

---

## Arquitectura *Transformer* (recordatorio)

- Modelo autoregresivo *(decoder-only)* para *next-token prediction*.  
- Componentes: **tokenization (BPE)**, **embedding** $W_E$, **positional embedding**, bloques con **Multi-Head Attention** y **MLP**, **residual stream**, **unembedding** $W_U$.  
- Atención (scaled dot-product):
$$
\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\!\left(\frac{QK^{\top}}{\sqrt{d_k}}\right)V
$$

---

`img/transformer_decoder.png`

---

## Autoregresión y *sampling*

- Objetivo: maximizar $p(x_1,\dots,x_N)=p(x_1)\prod_{n=2}^N p(x_n|x_{<n})$  
- A la hora de amostrar: *greedy*, *top-k*, *nucleus* (p).

---

## *Residual stream* (flujo residual)

Cada bloque suma su contribución a un vector de estado:
$$
\mathbf{x}_{i} = f_i(\mathbf{x}_{i-1}) + \mathbf{x}_{i-1}
$$

- Permite **memoria acumulativa** y mitiga *vanishing gradients*.  
- Las salidas finales (logits) son suma de **contribuciones** de atención y MLP a lo largo del *residual stream*.

---

## Multi-Head Attention (MHA)

- Proyecciones: $W^h_Q,\;W^h_K,\;W^h_V,\;W^h_O$
- Dimensiones: $d_{\text{model}}, d_{\text{head}}, n_{\text{head}}$  
- **Intuición**: distintas *heads* capturan **relaciones** complementarias.

---

## De *weights* a **circuitos**

Definiciones útiles por *head* $h$:

- **Matriz QK**: $W^{h}_{\text{QK}} = W^{h}_Q (W^{h}_K)^{\top}$ → *de dónde* y *hacia dónde* mira la atención.  
- **Matriz OV**: $W^{h}_{\text{OV}} = W^{h}_V W^{h}_O$ → **qué** información se transfiere por el *residual stream*.  
- **Circuitos completos** (de vocab a vocab):  
  - QK: $W_E W^{h}_{\text{QK}} W_E^{\top}$  
  - OV: $W_E W^{h}_{\text{OV}} W_U$

---

## *Attention patterns* típicos

- **Previous-token head**: mira al *token* inmediatamente anterior.  
- **Current-token head**: copia información del *token* actual.  
- **First-token head**: referencia al primer *token* (*BOS* / `<|endoftext|>`).

> Útiles para construir **circuitos** más complejos.

---

`img/attention_pattern.png`

---

## **Induction Heads** (patrón de inducción)

- Comportamiento: dada la repetición `[a][b] ... [a] → [b]`.  
- Requieren ≥2 capas.  
- **Emergen** con escala de datos/modelo.  
- *Circuito de inducción* (típico):
  1. *Previous-token head* establece alineación (QK).
  2. *Induction head* hace **K-composition** y **OV-copy** del siguiente *token*.

---

`img/repeated_seq.png`

---

## Ingeniería inversa del circuito **OV**

Ejemplo para copiar **B** tras ver `A B ... A`:

- Si $b$ es *one-hot* de **B**:
  - $b^{\top} W_E$ = *embedding* de **B**  
  - $b^{\top} W_E W^{h}_{\text{OV}}$ = **lo movido** a la posición destino  
  - $b^{\top} W_E W^{h}_{\text{OV}} W_U$ = **logits** inducidos (copia de **B**)

=> Diagonal fuerte ≈ *current-token head* (copia).

---

## Herramientas de interpretabilidad

- **Direct Logit Attribution (DLA)**: aplicar *unembedding* y normalización a salidas intermedias para descomponer **logits** por componente.  
- **Activation Patching**: injertar activaciones de una corrida “correcta” en una “corrompida” y medir recuperación de desempeño.  
- **Path/Connection Patching**: injertar **aristas** específicas (*head A* → *head B*) para aislar **circuitos**.

---

`img/activation-patching.png`

---

`img/path-patching.png`

---

# Caso de estudio: **IOI** (Indirect Object Identification)

**Tarea**: completar el objeto indirecto en frases como:  
“Juan confiaba en __” → **María** (no “Juan”).

**Métrica**: *logit difference* entre el *token* correcto (**María**) y el distractor (**Juan**).

---

## IOI: visión de alto nivel

- *Heads* de **tokens duplicados** (DTH): detectan que “Juan” aparece dos veces y marcan su posición.  
- *S-inhibition heads* (SIH): **inhiben** el nombre repetido (evitan autocorrección al sujeto).  
- *Name-mover heads* (NMH): mueven el **nombre correcto** (no repetido) al lugar de predicción.

> **Circuito IOI** = DTH + SIH + NMH (con *backup heads*).

---

## IOI: técnicas aplicadas

- **DLA por head** → cuantificar contribución a *logit diff*.  
- **Activation patching** entre *prompts* correctos y corrompidos.  
- **Path patching** para confirmar rutas DTH→SIH→NMH.  
- **Ablations** (apagado selectivo de heads) para validar redundancias.

---

## Superposición (*Superposition*)

**Fenómeno**: el modelo representa **más *features*** que dimensiones del espacio latente → **interferencia** y **polisemia**.

- *Toy model* ReLU (2D escondido, 5 *features*) muestra transición: con mayor **esparsidad** de *features*, el modelo **comprime** más en menos dimensiones:
$$
h=Wx,\quad x'=\mathrm{ReLU}(W^{\top}h+b),\quad
\mathcal{L}=\frac{1}{BF}\sum_x \sum_i I_i (x_i-x'_i)^2
$$

---

`img/superposition.png`

---

`img/superposition_correlation.png`

---

## Superposición vs Polisemia

- **Polisemia**: un neurón activa para múltiples *features*.  
- **Superposición**: *features* > dimensiones ⇒ **implica** polisemia (no al revés).

---

## *Sparse Autoencoders* (SAE)

**Idea**: entrenar **autoencoders esparsos** sobre **activaciones internas** para *desmezclar* *features* superpuestas en un espacio **más grande y esparso** ⇒ **monosemántico**.

- Pérdida típica: reconstrucción ($\ell_2$) + esparsidad ($\ell_1$ en el código).
- Se aplican a capas MLP/atención intermedias.

---

`img/superpositionhip.png`

---

`img/anthropic.png`

---

## Hipótesis de la superposición

> Redes pequeñas “simulan” redes grandes y esparsas aprovechando esparsidad de *features* y alta dimensionalidad.  
Los **SAE** intentarían **invertir** esa proyección para recuperar *features* interpretables.

---

## Resultados recientes (Anthropic: Scaling Monosemanticity)

- Demuestran **features interpretables** a gran escala en Claude 3 Sonnet via **SAE**.  
- Posibilidad de **editar** *features* (aumentar/disminuir) y observar efectos coherentes en el modelo.  
- Primer avance convincente de **monosemanticidad** en un **LLM de producción**.

---

<!-- ## Ecosistema y *tooling*

- **TransformerLens**: biblioteca para *mechanistic interpretability* (cachear activaciones, editar *hooks*, etc.).  
- ARENA 3.0: material práctico con notebooks y retos.

--- -->

## Limitaciones y riesgos

- **Escalabilidad**: *reverse engineering* completo sigue siendo difícil.  
- **Fragilidad**: circuitos pueden depender del *prompt distribution*.  
- **Métricas**: cuidado con *emergent abilities* y discontinuidades métricas.  
- **Generalización**: circuitos en GPT-2 small vs modelos más grandes.

---

<!-- ## Recomendaciones prácticas

- Empezar por **circuitos simples** (induction, IOI).  
- Medir siempre **logit attribution** + **patching**.  
- Documentar *heads* por patrón (previous/current/first-token).  
- Validar con **ablation** y **corridas adversariales**.

---

## Ejercicios sugeridos

1) Detectar *induction heads* y visualizar $W_{\text{pos}} W_{\text{QK}} W_{\text{pos}}^{\top}$.  
2) DLA por *head* en IOI y *activation patching*.  
3) Entrenar un SAE sobre activaciones MLP (capa media) y etiquetar *features*.

--- -->

## Conclusiones

- *Mechanistic interpretability* ofrece **mapas** de cómo piensan los *transformers*.  
- **Circuitos** (QK/OV) y **técnicas** (DLA, patching) permiten **causalizar** hipótesis.  
- **Superposición** explica polisemia; **SAE** abre la puerta a *features* **monosemánticas** en LLMs grandes.

---

## Referencias (selección)

- Vaswani et al., **Attention Is All You Need** (2017). 
- Nanda et al., **A Mathematical Framework for Transformer Circuits** (2021).
- Wang et al., **Interpretability in the Wild: a Circuit for IOI** (2022).
- Elhage et al., **Toy Models of Superposition** (2022).
- Conerly et al., **Scaling Monosemanticity** (2024).

---

## Ecosistema y *tooling*

- **[TransformerLens](https://github.com/TransformerLensOrg/TransformerLens)**: Library for MechInterp of GPT-style Language Models.
- **[CircuitsVis](https://github.com/TransformerLensOrg/CircuitsVis)**: MechInterp  Visualizations using React.
- **[SAELens](https://github.com/jbloomAus/SAELens)**: Library for Training Sparse Autoencoders on Language Models.
- **[ARENA 3.0](https://github.com/callummcdougall/ARENA_3.0)**: Exercises and Streamlit pages for the ARENA program.
- **[Neuronpedia](https://github.com/hijohnnylin/neuronpedia)**: Open source MechInterp platform.
- **[Circuit Tracer](https://github.com/safety-research/circuit-tracer)**: Library for finding circuits using features from MLP transcoders.
- **[NNSight](https://github.com/ndif-team/nnsight)**: Package for interpret and manipulate internals of deep learned models.
