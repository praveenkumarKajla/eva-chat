import '@testing-library/jest-dom';
import { render, act } from '@testing-library/react';
import { AuthProvider, AuthContext, AuthContextType } from './AuthContext';

describe('AuthProvider', () => {
  it('provides the correct context value', () => {
    let contextValue: AuthContextType | undefined;
    render(
      <AuthProvider>
        <AuthContext.Consumer>
          {value => {
            contextValue = value;
            return null;
          }}
        </AuthContext.Consumer>
      </AuthProvider>
    );

    expect(contextValue).toBeDefined();
    expect(contextValue!.user).toBeNull();
    expect(typeof contextValue!.login).toBe('function');
    expect(typeof contextValue!.logout).toBe('function');
  });

  it('updates user on login and logout', () => {
    let contextValue: AuthContextType | undefined;
    const { rerender } = render(
      <AuthProvider>
        <AuthContext.Consumer>
          {(value) => {
            contextValue = value;
            return null;
          }}
        </AuthContext.Consumer>
      </AuthProvider>
    );

    // Ensure contextValue is defined before using it
    expect(contextValue).toBeDefined();
    
    act(() => {
      contextValue!.login('test-token');
    });
    rerender(
      <AuthProvider>
        <AuthContext.Consumer>
          {(value) => {
            contextValue = value!;
            return null;
          }}
        </AuthContext.Consumer>
      </AuthProvider>
    );
    expect(contextValue?.user).toEqual({ token: 'test-token' });

    act(() => {
      contextValue?.logout();
    });
    rerender(
      <AuthProvider>
        <AuthContext.Consumer>
          {(value) => {
            contextValue = value!;
            return null;
          }}
        </AuthContext.Consumer>
      </AuthProvider>
    );
    expect(contextValue?.user).toBeNull();
  });
});