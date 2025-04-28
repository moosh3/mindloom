import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatStore, Conversation, Message, Agent } from '../types';

const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      conversations: [],
      currentConversation: null,

      addConversation: (agent: Agent) => {
        const conversation: Conversation = {
          id: Date.now().toString(),
          agentId: agent.id,
          title: agent.name,
          lastMessageTime: new Date(),
          messages: [],
          createdAt: new Date(),
          updatedAt: new Date(),
        };

        set(state => ({
          conversations: [conversation, ...state.conversations],
          currentConversation: conversation,
        }));

        return conversation;
      },

      addMessage: (conversationId: string, message: Omit<Message, 'id'>) => {
        const newMessage: Message = {
          id: Date.now().toString(),
          ...message,
        };

        set(state => {
          const conversations = state.conversations.map(conv => {
            if (conv.id === conversationId) {
              return {
                ...conv,
                messages: [...conv.messages, newMessage],
                lastMessage: message.content,
                lastMessageTime: message.timestamp,
                updatedAt: new Date(),
              };
            }
            return conv;
          });

          const currentConversation = state.currentConversation?.id === conversationId
            ? {
                ...state.currentConversation,
                messages: [...state.currentConversation.messages, newMessage],
                lastMessage: message.content,
                lastMessageTime: message.timestamp,
                updatedAt: new Date(),
              }
            : state.currentConversation;

          return {
            conversations,
            currentConversation,
          };
        });
      },

      setCurrentConversation: (conversationId: string) => {
        set(state => ({
          currentConversation: state.conversations.find(c => c.id === conversationId) || null,
        }));
      },

      clearConversation: (conversationId: string) => {
        set(state => ({
          conversations: state.conversations.filter(c => c.id !== conversationId),
          currentConversation: state.currentConversation?.id === conversationId
            ? null
            : state.currentConversation,
        }));
      },

      clearAllConversations: () => {
        set({
          conversations: [],
          currentConversation: null,
        });
      },
    }),
    {
      name: 'chat-storage',
    }
  )
);

export default useChatStore;