const supabase = {
  auth: {
    signInWithPassword: async () => ({ 
      data: { 
        user: {
          id: 'mock-user-id',
          email: 'mock@example.com',
          user_metadata: {
            name: 'Mock User'
          }
        } 
      }, 
      error: null 
    }),
    signUp: async () => ({ 
      data: { 
        user: {
          id: 'mock-user-id',
          email: 'mock@example.com',
          user_metadata: {
            name: 'Mock User'
          }
        } 
      }, 
      error: null 
    }),
    signOut: async () => ({ error: null }),
  },
};

export { supabase };