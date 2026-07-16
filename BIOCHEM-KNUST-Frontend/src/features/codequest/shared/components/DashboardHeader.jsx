const DashboardHeader = ({ title, subtitle, rightContent }) => {
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          {subtitle && <p className="text-gray-600 mt-1">{subtitle}</p>}
        </div>
        {rightContent && <div>{rightContent}</div>}
      </div>
    </div>
  );
};

export default DashboardHeader;
