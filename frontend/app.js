
        class SupOneAI {
            constructor() {
                this.chatBody = document.getElementById('chatContent');
                this.messageForm = document.getElementById('messageForm');
                this.userInput = document.getElementById('userInput');
                this.typingIndicator = document.getElementById('typingIndicator');
                this.suggestionsBox = document.getElementById('suggestionsBox');
                
                this.init();
            }

            init() {
                this.messageForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.handleUserAction();
                });

                document.querySelectorAll('.suggestion-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const text = btn.getAttribute('data-msg');
                        this.handleUserAction(text);
                        this.suggestionsBox.style.display = 'none';
                    });
                });
            }

            async handleUserAction(text = null) {
                const message = text || this.userInput.value.trim();
                if (!message) return;

                this.addMessage(message, 'user');
                this.userInput.value = '';
                this.showTyping(true);

                // Simulation d'une réponse API
                setTimeout(() => {
                    this.showTyping(false);
                    this.generateBotResponse(message);
                }, 1500);
            }

            addMessage(text, sender) {
                const container = document.createElement('div');
                container.className = 'message-container';
                const bubble = document.createElement('div');
                bubble.className = sender === 'user' ? 'msg-user' : 'msg-bot';
                bubble.innerHTML = text;
                container.appendChild(bubble);
                this.chatBody.appendChild(container);
                this.chatBody.scrollTop = this.chatBody.scrollHeight;
            }
                /*Generation d'un exemple de reponse*/
            generateBotResponse(input) {
                let response = "Je suis votre assistant SUP'PTIC. Je n'ai pas la réponse précise, mais je peux vous rediriger vers l'administration.";
                const lowInput = input.toLowerCase();

                if (lowInput.includes('histoire')) response = "L'École Nationale Supérieure des Postes, des Télécommunications et des TIC (SUP'PTIC) forme les cadres de l'économie numérique depuis des décennies.";
                if (lowInput.includes('chambre')) response = "Pour les logements, veuillez consulter le service de la scolarité pour connaître les disponibilités des cités universitaires.";
                if (lowInput.includes('club')) response = "Vous pouvez rejoindre le club de Robotique, de Musique ou d'Entrepreneuriat dès la rentrée !";
                if (lowInput.includes('question')) response = "Je suis votre assistant dedie poser vos questions et j'y repondrais !";

                this.addMessage(response, 'bot');
            }

            showTyping(show) {
                this.typingIndicator.style.display = show ? 'block' : 'none';
                this.chatBody.scrollTop = this.chatBody.scrollHeight;
            }
        }

        document.addEventListener('DOMContentLoaded', () => new SupOneAI());
        
        
if (typeof module !== 'undefined') {
    module.exports = SupOneAI;
}