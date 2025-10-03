/**
 * Approval Queue component for SQL-Guard frontend
 * Manages template approval workflow and reviewer assignments
 */
import React, { useState, useCallback } from 'react';
import { CheckCircle, XCircle, Eye, Clock, User, MessageSquare, Filter, Search } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Textarea } from '../ui/textarea';
import { Alert, AlertDescription } from '../ui/alert';
import { useAuth } from '../../hooks/useAuth';

interface ApprovalRequest {
  id: string;
  template_id: string;
  template_name: string;
  template_version: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  submitted_by: string;
  submitted_at: string;
  assigned_to?: string;
  reviewed_at?: string;
  reviewer_comment?: string;
  changes_summary?: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
}

interface ApprovalQueueProps {
  className?: string;
}

export function ApprovalQueue({ className }: ApprovalQueueProps) {
  const { user, hasPermission } = useAuth();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [selectedApproval, setSelectedApproval] = useState<ApprovalRequest | null>(null);
  const [reviewComment, setReviewComment] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const canApproveTemplates = hasPermission('approve_templates');
  const canViewApprovals = hasPermission('view_approval_requests');

  // Mock data - in real implementation, this would come from API
  const mockApprovals: ApprovalRequest[] = [
    {
      id: '1',
      template_id: 't1',
      template_name: 'User Activity Report',
      template_version: 2,
      status: 'PENDING',
      submitted_by: 'john.doe@company.com',
      submitted_at: '2024-01-15T10:30:00Z',
      assigned_to: user?.email,
      priority: 'HIGH',
      changes_summary: 'Added new columns for user engagement metrics',
    },
    {
      id: '2',
      template_id: 't2',
      template_name: 'Sales Analytics',
      template_version: 1,
      status: 'PENDING',
      submitted_by: 'jane.smith@company.com',
      submitted_at: '2024-01-15T09:15:00Z',
      priority: 'MEDIUM',
      changes_summary: 'Initial template for sales data analysis',
    },
    {
      id: '3',
      template_id: 't3',
      template_name: 'Customer Segmentation',
      template_version: 3,
      status: 'APPROVED',
      submitted_by: 'mike.wilson@company.com',
      submitted_at: '2024-01-14T16:45:00Z',
      assigned_to: 'admin@company.com',
      reviewed_at: '2024-01-15T08:30:00Z',
      reviewer_comment: 'Approved with minor suggestions for optimization',
      priority: 'LOW',
      changes_summary: 'Updated segmentation criteria based on new business rules',
    },
  ];

  // Filter approvals based on search and filters
  const filteredApprovals = mockApprovals.filter(approval => {
    const matchesSearch = approval.template_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         approval.submitted_by.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || approval.status === statusFilter;
    const matchesPriority = priorityFilter === 'all' || approval.priority === priorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  const handleApprove = useCallback(async (approvalId: string) => {
    setIsProcessing(true);
    try {
      // TODO: Implement actual approval API call
      console.log('Approving template:', approvalId, 'with comment:', reviewComment);
      setReviewComment('');
      setSelectedApproval(null);
    } catch (error) {
      console.error('Approval failed:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [reviewComment]);

  const handleReject = useCallback(async (approvalId: string) => {
    if (!reviewComment.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }

    setIsProcessing(true);
    try {
      // TODO: Implement actual rejection API call
      console.log('Rejecting template:', approvalId, 'with comment:', reviewComment);
      setReviewComment('');
      setSelectedApproval(null);
    } catch (error) {
      console.error('Rejection failed:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [reviewComment]);

  const getPriorityBadge = (priority: string) => {
    const priorityConfig = {
      LOW: { variant: 'secondary' as const, color: 'text-gray-600' },
      MEDIUM: { variant: 'outline' as const, color: 'text-blue-600' },
      HIGH: { variant: 'default' as const, color: 'text-orange-600' },
      URGENT: { variant: 'destructive' as const, color: 'text-red-600' },
    };

    const config = priorityConfig[priority as keyof typeof priorityConfig] || priorityConfig.LOW;

    return (
      <Badge variant={config.variant} className={config.color}>
        {priority}
      </Badge>
    );
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      PENDING: { variant: 'outline' as const, icon: Clock, label: 'Pending' },
      APPROVED: { variant: 'default' as const, icon: CheckCircle, label: 'Approved' },
      REJECTED: { variant: 'destructive' as const, icon: XCircle, label: 'Rejected' },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.PENDING;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (!canViewApprovals) {
    return (
      <div className={`space-y-4 ${className}`}>
        <Alert>
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            You don't have permission to view approval requests.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Approval Queue</h2>
          <p className="text-muted-foreground">
            Review and approve SQL template changes
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            {filteredApprovals.filter(a => a.status === 'PENDING').length} pending
          </Badge>
          <Badge variant="outline">
            {filteredApprovals.length} total
          </Badge>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search templates or submitter..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
              </SelectContent>
            </Select>
            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priority</SelectItem>
                <SelectItem value="URGENT">Urgent</SelectItem>
                <SelectItem value="HIGH">High</SelectItem>
                <SelectItem value="MEDIUM">Medium</SelectItem>
                <SelectItem value="LOW">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Approvals List */}
      <div className="space-y-4">
        {filteredApprovals.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Clock className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No approval requests found</h3>
                <p className="text-muted-foreground">
                  {searchTerm || statusFilter !== 'all' || priorityFilter !== 'all'
                    ? 'Try adjusting your search or filter criteria'
                    : 'No approval requests are currently pending'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredApprovals.map((approval) => (
            <Card key={approval.id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold">{approval.template_name}</h3>
                      <Badge variant="outline">v{approval.template_version}</Badge>
                      {getStatusBadge(approval.status)}
                      {getPriorityBadge(approval.priority)}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4" />
                        <span>Submitted by: {approval.submitted_by}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4" />
                        <span>Submitted: {formatDate(approval.submitted_at)}</span>
                      </div>
                      {approval.assigned_to && (
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4" />
                          <span>Assigned to: {approval.assigned_to}</span>
                        </div>
                      )}
                      {approval.reviewed_at && (
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4" />
                          <span>Reviewed: {formatDate(approval.reviewed_at)}</span>
                        </div>
                      )}
                    </div>

                    {approval.changes_summary && (
                      <div className="bg-muted p-3 rounded-lg">
                        <p className="text-sm">
                          <span className="font-medium">Changes:</span> {approval.changes_summary}
                        </p>
                      </div>
                    )}

                    {approval.reviewer_comment && (
                      <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
                        <p className="text-sm text-blue-800">
                          <span className="font-medium">Reviewer Comment:</span> {approval.reviewer_comment}
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4 mr-2" />
                          Review
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl">
                        <DialogHeader>
                          <DialogTitle>Review Template: {approval.template_name}</DialogTitle>
                        </DialogHeader>
                        <Tabs defaultValue="overview" className="mt-4">
                          <TabsList>
                            <TabsTrigger value="overview">Overview</TabsTrigger>
                            <TabsTrigger value="changes">Changes</TabsTrigger>
                            <TabsTrigger value="review">Review</TabsTrigger>
                          </TabsList>
                          
                          <TabsContent value="overview" className="mt-4 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <h4 className="font-medium mb-2">Template Information</h4>
                                <div className="space-y-2 text-sm">
                                  <div><span className="font-medium">Name:</span> {approval.template_name}</div>
                                  <div><span className="font-medium">Version:</span> {approval.template_version}</div>
                                  <div><span className="font-medium">Status:</span> {approval.status}</div>
                                  <div><span className="font-medium">Priority:</span> {approval.priority}</div>
                                </div>
                              </div>
                              <div>
                                <h4 className="font-medium mb-2">Submission Details</h4>
                                <div className="space-y-2 text-sm">
                                  <div><span className="font-medium">Submitted by:</span> {approval.submitted_by}</div>
                                  <div><span className="font-medium">Submitted at:</span> {formatDate(approval.submitted_at)}</div>
                                  {approval.assigned_to && (
                                    <div><span className="font-medium">Assigned to:</span> {approval.assigned_to}</div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </TabsContent>
                          
                          <TabsContent value="changes" className="mt-4">
                            <div className="space-y-4">
                              <h4 className="font-medium">Changes Summary</h4>
                              <div className="bg-muted p-4 rounded-lg">
                                <p>{approval.changes_summary || 'No changes summary provided'}</p>
                              </div>
                              {/* TODO: Add diff view of template changes */}
                            </div>
                          </TabsContent>
                          
                          <TabsContent value="review" className="mt-4">
                            <div className="space-y-4">
                              <div>
                                <label className="text-sm font-medium mb-2 block">Review Comment</label>
                                <Textarea
                                  placeholder="Add your review comment..."
                                  value={reviewComment}
                                  onChange={(e) => setReviewComment(e.target.value)}
                                  rows={4}
                                />
                              </div>
                              
                              {canApproveTemplates && approval.status === 'PENDING' && (
                                <div className="flex items-center gap-2">
                                  <Button
                                    onClick={() => handleApprove(approval.id)}
                                    disabled={isProcessing}
                                    className="flex items-center gap-2"
                                  >
                                    <CheckCircle className="h-4 w-4" />
                                    Approve
                                  </Button>
                                  <Button
                                    onClick={() => handleReject(approval.id)}
                                    disabled={isProcessing}
                                    variant="destructive"
                                    className="flex items-center gap-2"
                                  >
                                    <XCircle className="h-4 w-4" />
                                    Reject
                                  </Button>
                                </div>
                              )}
                            </div>
                          </TabsContent>
                        </Tabs>
                      </DialogContent>
                    </Dialog>

                    {canApproveTemplates && approval.status === 'PENDING' && (
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          onClick={() => handleApprove(approval.id)}
                          disabled={isProcessing}
                          className="flex items-center gap-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => {
                            const comment = prompt('Please provide a reason for rejection:');
                            if (comment) {
                              setReviewComment(comment);
                              handleReject(approval.id);
                            }
                          }}
                          disabled={isProcessing}
                          className="flex items-center gap-1"
                        >
                          <XCircle className="h-3 w-3" />
                          Reject
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}