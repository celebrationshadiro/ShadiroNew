import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { admin } from '../../lib/api';
import { Search, Lock, Unlock, Shield, Users, Loader2, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [blockingId, setBlockingId] = useState(null);
  const [activatingId, setActivatingId] = useState(null);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        limit: 100,
        ...(search && { search }),
        ...(roleFilter && { role: roleFilter }),
      };
      const res = await admin.getUsers(params);
      const rawUsers = res?.data;
      const usersList = Array.isArray(rawUsers)
        ? rawUsers
        : Array.isArray(rawUsers?.items)
          ? rawUsers.items
          : [];

      // Client-side filter for active status
      let filtered = usersList;
      if (activeFilter === 'active') {
        filtered = filtered.filter((u) => u.is_active !== false && u.is_blocked !== true);
      } else if (activeFilter === 'blocked') {
        filtered = filtered.filter((u) => u.is_active === false || u.is_blocked === true);
      }
      
      setUsers(filtered);
    } catch (err) {
      console.error('Failed to load users:', err);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter, activeFilter]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleBlockUser = async (userId) => {
    const reason = prompt('Enter reason for blocking:');
    if (!reason) return;

    setBlockingId(userId);
    try {
      await admin.blockUser(userId, reason);
      toast.success('User blocked successfully');
      loadUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to block user');
    } finally {
      setBlockingId(null);
    }
  };

  const handleActivateUser = async (userId) => {
    setActivatingId(userId);
    try {
      await admin.activateUser(userId);
      toast.success('User activated successfully');
      loadUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to activate user');
    } finally {
      setActivatingId(null);
    }
  };

  const getRoleColor = (role) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-800',
      vendor: 'bg-blue-100 text-blue-800',
      customer: 'bg-green-100 text-green-800',
    };
    return colors[role] || 'bg-stone-100 text-stone-800';
  };

  const getUserStats = () => {
    const total = users.length;
    const admins = users.filter(u => u.role === 'admin').length;
    const vendors = users.filter(u => u.role === 'vendor').length;
    const regularUsers = users.filter(u => u.role === 'customer' || u.role === 'user').length;
    const blocked = users.filter(u => u.is_active === false || u.is_blocked === true).length;
    return { total, admins, vendors, regularUsers, blocked };
  };

  const stats = getUserStats();

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Users className="w-8 h-8" /> User Management
        </h1>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-8">
        <Card className="p-4 bg-gradient-to-br from-stone-50 to-stone-100">
          <p className="text-xs text-stone-600 font-medium">Total Users</p>
          <p className="text-2xl font-bold text-stone-900">{stats.total}</p>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-purple-50 to-purple-100">
          <p className="text-xs text-purple-600 font-medium">Admins</p>
          <p className="text-2xl font-bold text-purple-900">{stats.admins}</p>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-blue-50 to-blue-100">
          <p className="text-xs text-blue-600 font-medium">Vendors</p>
          <p className="text-2xl font-bold text-blue-900">{stats.vendors}</p>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-green-50 to-green-100">
          <p className="text-xs text-green-600 font-medium">Users</p>
          <p className="text-2xl font-bold text-green-900">{stats.regularUsers}</p>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-red-50 to-red-100">
          <p className="text-xs text-red-600 font-medium">Blocked</p>
          <p className="text-2xl font-bold text-red-900">{stats.blocked}</p>
        </Card>
      </div>

      {/* Filters */}
      <div className="mb-6 space-y-3 md:space-y-0 md:flex gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 w-5 h-5 text-stone-400" />
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-stone-200 rounded-lg focus:outline-none focus:border-black focus:ring-1 focus:ring-black"
          />
        </div>

        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-4 py-2 border border-stone-200 rounded-lg focus:outline-none focus:border-black"
        >
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="vendor">Vendor</option>
          <option value="customer">Customer</option>
        </select>

        <select
          value={activeFilter}
          onChange={(e) => setActiveFilter(e.target.value)}
          className="px-4 py-2 border border-stone-200 rounded-lg focus:outline-none focus:border-black"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="blocked">Blocked</option>
        </select>
      </div>

      {/* Users List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-stone-400" />
        </div>
      ) : users.length === 0 ? (
        <Card className="p-8 text-center">
          <Users className="w-12 h-12 mx-auto text-stone-300 mb-3" />
          <p className="text-stone-500">No users found matching your filters</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {users.map((u) => (
            <Card key={u.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Shield className="w-5 h-5 text-stone-400" />
                    <div>
                      <h3 className="font-semibold text-stone-900">{u.name}</h3>
                      <p className="text-sm text-stone-500">{u.email}</p>
                    </div>
                  </div>
                  {u.phone && (
                    <p className="text-xs text-stone-500 ml-8">{u.phone}</p>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <Badge className={getRoleColor(u.role)}>
                    {u.role}
                  </Badge>

                  {u.is_active === false && (
                    <Badge className="bg-red-100 text-red-800">Blocked</Badge>
                  )}

                  {u.is_active !== false ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleBlockUser(u.id)}
                      disabled={blockingId === u.id}
                      className="border-red-200 text-red-600 hover:bg-red-50"
                    >
                      {blockingId === u.id ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin mr-1" /> Blocking
                        </>
                      ) : (
                        <>
                          <Lock className="w-4 h-4 mr-1" /> Block
                        </>
                      )}
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleActivateUser(u.id)}
                      disabled={activatingId === u.id}
                      className="border-green-200 text-green-600 hover:bg-green-50"
                    >
                      {activatingId === u.id ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin mr-1" /> Activating
                        </>
                      ) : (
                        <>
                          <Unlock className="w-4 h-4 mr-1" /> Activate
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </div>

              {u.block_reason && (
                <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Block Reason: {u.block_reason}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminUsers;
