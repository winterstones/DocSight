from rest_framework import serializers


class SearchRequestSerializer(serializers.Serializer):
    q          = serializers.CharField(min_length=1, max_length=500)
    tags       = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    file_types = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    page       = serializers.IntegerField(min_value=1, default=1)
    page_size  = serializers.IntegerField(min_value=1, max_value=100, default=20)


class SearchResultSerializer(serializers.Serializer):
    id              = serializers.CharField()
    title           = serializers.CharField()
    content_preview = serializers.CharField()
    file_type       = serializers.CharField()
    tags            = serializers.ListField(child=serializers.CharField())
    score           = serializers.FloatField()
    thumbnail_url   = serializers.URLField(allow_null=True)


class SearchResponseSerializer(serializers.Serializer):
    results   = SearchResultSerializer(many=True)
    total     = serializers.IntegerField()
    query     = serializers.CharField()
    page      = serializers.IntegerField()
    page_size = serializers.IntegerField()


class ChatRequestSerializer(serializers.Serializer):
    question     = serializers.CharField(min_length=3, max_length=1000)
    document_ids = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class ChatResponseSerializer(serializers.Serializer):
    answer  = serializers.CharField()
    sources = SearchResultSerializer(many=True)
