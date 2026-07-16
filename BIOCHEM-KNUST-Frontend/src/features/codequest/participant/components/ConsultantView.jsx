const ConsultantView = ({ groupData }) => {
  const consultant = groupData?.consultant || {};

  return (
    <div className="max-w-4xl mx-auto">
      {consultant.name ? (
        <div className="space-y-6">
          {/* Consultant Profile Card */}
          <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl shadow-lg p-8 text-white">
            <div className="flex items-center gap-6">
              {consultant.profile_picture ? (
                <img
                  src={consultant.profile_picture}
                  alt={consultant.name}
                  className="w-24 h-24 rounded-full border-4 border-white/30"
                />
              ) : (
                <div className="w-24 h-24 bg-white/20 rounded-full flex items-center justify-center text-4xl font-bold">
                  {consultant.name?.charAt(0) || "C"}
                </div>
              )}
              <div className="flex-1">
                <h2 className="text-3xl font-bold mb-2">{consultant.name}</h2>
                <p className="text-purple-100 mb-1">
                  {consultant.student_id} • {consultant.year}
                </p>
                <p className="text-purple-100">{consultant.email}</p>
              </div>
            </div>
          </div>

          {/* Expertise Areas */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              Expertise Areas
            </h3>
            <div className="flex flex-wrap gap-2">
              {consultant.expertise_areas?.split(", ").map((area, index) => (
                <span
                  key={index}
                  className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg font-medium"
                >
                  {area}
                </span>
              )) || <p className="text-gray-500">No expertise areas listed</p>}
            </div>
          </div>

          {/* Bio */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">About</h3>
            <p className="text-gray-700 leading-relaxed">
              {consultant.bio || "No bio available."}
            </p>
          </div>

          {/* Contact Card */}
          <div className="bg-blue-50 rounded-xl p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              Get in Touch
            </h3>
            <div className="space-y-2">
              <p className="flex items-center gap-2 text-gray-700">
                <span>📧</span>
                <a
                  href={`mailto:${consultant.email}`}
                  className="text-blue-600 hover:underline"
                >
                  {consultant.email}
                </a>
              </p>
              {consultant.phone_number && (
                <p className="flex items-center gap-2 text-gray-700">
                  <span>📱</span>
                  {consultant.phone_number}
                </p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-md p-12 text-center">
          <div className="text-6xl mb-4">👨‍🏫</div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            No Consultant Assigned Yet
          </h3>
          <p className="text-gray-600">
            A consultant will be assigned to your group soon.
          </p>
        </div>
      )}
    </div>
  );
};

export default ConsultantView;
