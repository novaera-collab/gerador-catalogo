import os
from gtts import gTTS
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)

# 1. Roteiro de narração baseado no tutorial
ROTEIRO = [
    {
        "texto": "Olá! Seja bem-vindo ao tutorial do Gerador de Encartes. Vamos ver como funciona o sistema.",
        "imagem": "avatar.png",  # Imagem do avatar falando
        "slide": None,
    },
    {
        "texto": "Existem duas formas de uso: A primeira é a integração via ERP, onde o ERP gera um arquivo CSV e chama o executável gerar_catalogo passing o CSV e a imagem final.",
        "imagem": "avatar.png",
        "slide": "opcao_erp.png",  # Print do encarte/CSV
    },
    {
        "texto": "A segunda opção é através do App Gestão Encarte. Primeiro, configure o banco de dados e salve os parâmetros do sistema.",
        "imagem": "avatar.png",
        "slide": "parametros_banco.png",  # Print da tela de Banco de Dados
    },
    {
        "texto": "Em seguida, defina os diretórios do sistema e a identidade visual, como logotipos, site e as cores do título, grid e preços.",
        "imagem": "avatar.png",
        "slide": "parametros_design.png",  # Print da tela de Diretórios e Design
    },
    {
        "texto": "Na Manutenção do Encarte, você cadastra os produtos, define o período da promoção e ajusta os preços das ofertas.",
        "imagem": "avatar.png",
        "slide": "manutencao_encarte.png",  # Print da tela de Manutenção
    },
    {
        "texto": "Para finalizar, escolha o contato, a tabela de preços e os saldos. Clique em Confirmar e Gerar Encarte para abrir o visualizador e disparar pelo WhatsApp!",
        "imagem": "avatar.png",
        "slide": "gerar_encarte.png",  # Print da janela Gerar Encarte
    },
]


def criar_video_tutorial():
    clips = []

    for index, etapa in enumerate(ROTEIRO):
        audio_file = f"temp_audio_{index}.mp3"

        # Gera o áudio com gTTS (Português)
        tts = gTTS(text=etapa["texto"], lang="pt", slow=False)
        tts.save(audio_file)

        # Carrega a duração do áudio gerado
        audio_clip = AudioFileClip(audio_file)
        duracao = audio_clip.duration

        # Configura o Avatar no canto da tela (posição fixa ou destaque)
        if os.path.exists(etapa["imagem"]):
            avatar_clip = (
                ImageClip(etapa["imagem"])
                .set_duration(duracao)
                .resize(height=300)
                .set_position(("right", "bottom"))
            )
        else:
            avatar_clip = None

        # Configura a imagem do slide/tela
        if etapa["slide"] and os.path.exists(etapa["slide"]):
            slide_clip = (
                ImageClip(etapa["slide"])
                .set_duration(duracao)
                .resize(width=800)
                .set_position(("left", "top"))
            )
        else:
            # Caso não tenha slide, cria uma tela neutra
            slide_clip = (
                ColorClip(size=(1280, 720), color=(30, 30, 30))
                .set_duration(duracao)
            )

        # Combina elementos da cena
        elementos = [slide_clip]
        if avatar_clip:
            elementos.append(avatar_clip)

        cena = CompositeVideoClip(elementos, size=(1280, 720))
        cena = cena.set_audio(audio_clip)

        clips.append(cena)

    # Concatena todas as cenas no vídeo final
    video_final = concatenate_videoclips(clips, method="compose")
    video_final.write_videofile(
        "tutorial_gerar_encarte.mp4", fps=24, codec="libx264"
    )

    # Limpeza de arquivos temporários de áudio
    for index in range(len(ROTEIRO)):
        temp_file = f"temp_audio_{index}.mp3"
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    criar_video_tutorial()
