import React from 'react';

export const Toaster = () => {
  return (
    <div className="fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]">
      {/* Toast notifications will be rendered here */}
    </div>
  );
};
