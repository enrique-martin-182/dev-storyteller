import React from 'react';
import { useAppContext } from '../contexts/AppContext';

function MessageDisplay() {
  const { message, error } = useAppContext();

  return (
    <>
      {message && <p className="success-message">{message}</p>}
      {error && <p className="error-message">{error}</p>}
    </>
  );
}

export default MessageDisplay;
