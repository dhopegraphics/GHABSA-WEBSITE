import React from 'react';
import { FiAlertCircle } from 'react-icons/fi';
import { Link } from 'react-router-dom';

function PageNotFound() {
  return (
    <main className="grid min-h-screen relative place-items-center bg-white px-6 py-24 sm:py-32 lg:px-8">
      <FiAlertCircle className="text-blue-300 -rotate-12 animate-ping text-[250px] absolute z-0 top-auto right-auto" />
      <div className="text-center z-10">
      <FiAlertCircle className="text-blue-300 -rotate-12 animate-bounce delay-500 text-[50px] w-full" />
        <p className="text-base font-semibold text-blue-600">404</p>
        <h1 className="mt-4 text-3xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          Page not found
        </h1>
        <p className="mt-6 text-base leading-7 text-gray-600 dark:text-gray-400">
          Sorry, we couldn’t find the page you’re looking for.
        </p>
        <div className="mt-10 flex items-center justify-center gap-x-6">
          <Link
            to="/"
            className="rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          >
            Go back home
          </Link>
          <Link to={'/contact-us'} className="text-sm font-semibold text-gray-900">
            Contact support <span aria-hidden="true">&rarr;</span>
          </Link>
        </div>
      </div>
    </main>
  );
}

export default PageNotFound;
